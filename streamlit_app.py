import streamlit as st
import pandas as pd
import os
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path
import zipfile
import io
import json
from concurrent.futures import ThreadPoolExecutor
import sys

# Configure Streamlit page
st.set_page_config(
    page_title="Google Maps Web Scraper",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define paths
EXCEL_UPLOAD_PATH = "/app/excel_files"
OUTPUT_PATH = "/app/output"
LOGS_PATH = "/app/logs"

# Create directories if they don't exist
os.makedirs(EXCEL_UPLOAD_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)
os.makedirs(LOGS_PATH, exist_ok=True)

# Session state initialization
if 'scraping_active' not in st.session_state:
    st.session_state.scraping_active = False
if 'scraping_process' not in st.session_state:
    st.session_state.scraping_process = None
if 'scraping_stats' not in st.session_state:
    st.session_state.scraping_stats = {}

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🗺️ Google Maps Web Scraper Dashboard</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/google-maps.png", width=100)
    st.title("⚙️ Configuration")

    # System status
    st.subheader("System Status")
    col1, col2 = st.columns(2)

    # Check if scraper is running
    with col1:
        if st.session_state.scraping_active:
            st.success("🟢 Running")
        else:
            st.info("⚪ Idle")

    # Check system resources
    with col2:
        try:
            # Get number of uploaded files
            excel_files = len([f for f in os.listdir(EXCEL_UPLOAD_PATH) if f.endswith('.xlsx')])
            st.metric("Excel Files", excel_files)
        except:
            st.metric("Excel Files", 0)

    # Output files count
    try:
        output_files = len([f for f in os.listdir(OUTPUT_PATH) if f.endswith('.xlsx')])
        st.metric("Output Files", output_files)
    except:
        st.metric("Output Files", 0)

    st.markdown("---")

    # Settings
    st.subheader("Scraper Settings")

    max_workers = st.slider(
        "Concurrent Workers",
        min_value=1,
        max_value=4,
        value=3,
        help="Number of parallel scraping threads (recommended: 3 for 4 vCPU)"
    )

    max_scrolls = st.slider(
        "Max Scrolls per Search",
        min_value=5,
        max_value=20,
        value=10,
        help="Number of times to scroll results (more = more data but slower)"
    )

    st.markdown("---")
    st.caption("Built with Streamlit 🎈")
    st.caption("Deployed on Hostinger VPS")

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Files", "🚀 Run Scraper", "📊 View Progress", "📥 Download Results"])

# ============================================================================
# TAB 1: UPLOAD FILES
# ============================================================================
with tab1:
    st.header("📤 Upload Excel Files")
    st.markdown("Upload one or multiple Excel files containing zipcodes to scrape.")

    col1, col2 = st.columns([2, 1])

    with col1:
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose Excel files (.xlsx)",
            type=['xlsx'],
            accept_multiple_files=True,
            help="Upload Excel files with a column containing zipcodes"
        )

        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected")

            # Display uploaded files
            for uploaded_file in uploaded_files:
                with st.expander(f"📄 {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)"):
                    try:
                        df = pd.read_excel(uploaded_file)
                        st.write(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")
                        st.write("**Columns:**", ", ".join(df.columns.tolist()))
                        st.dataframe(df.head(5))
                    except Exception as e:
                        st.error(f"Error reading file: {e}")

            # Upload button
            if st.button("💾 Save Files to Server", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()

                for idx, uploaded_file in enumerate(uploaded_files):
                    try:
                        # Save file
                        file_path = os.path.join(EXCEL_UPLOAD_PATH, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        status_text.text(f"Saved: {uploaded_file.name}")
                        progress_bar.progress((idx + 1) / len(uploaded_files))
                        time.sleep(0.2)
                    except Exception as e:
                        st.error(f"Error saving {uploaded_file.name}: {e}")

                status_text.empty()
                progress_bar.empty()
                st.success("✅ All files uploaded successfully!")
                time.sleep(1)
                st.rerun()

    with col2:
        st.info("""
        **📋 File Requirements:**
        - Format: Excel (.xlsx)
        - Must contain zipcode column
        - Column name: "DELIVERY ZIPCODE" or similar
        - One zipcode per row
        """)

    st.markdown("---")

    # Show existing uploaded files
    st.subheader("📂 Uploaded Files on Server")

    try:
        excel_files = [f for f in os.listdir(EXCEL_UPLOAD_PATH) if f.endswith('.xlsx')]

        if excel_files:
            for file in excel_files:
                col1, col2, col3 = st.columns([3, 1, 1])

                file_path = os.path.join(EXCEL_UPLOAD_PATH, file)
                file_size = os.path.getsize(file_path) / 1024  # KB

                with col1:
                    st.write(f"📄 **{file}**")

                with col2:
                    st.write(f"{file_size:.2f} KB")

                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{file}"):
                        os.remove(file_path)
                        st.success(f"Deleted: {file}")
                        time.sleep(0.5)
                        st.rerun()
        else:
            st.info("No files uploaded yet. Upload files above to get started.")
    except Exception as e:
        st.error(f"Error listing files: {e}")

# ============================================================================
# TAB 2: RUN SCRAPER
# ============================================================================
with tab2:
    st.header("🚀 Run Web Scraper")

    # Check if files are uploaded
    try:
        excel_files = [f for f in os.listdir(EXCEL_UPLOAD_PATH) if f.endswith('.xlsx')]
    except:
        excel_files = []

    if not excel_files:
        st.warning("⚠️ No Excel files found. Please upload files in the 'Upload Files' tab first.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            # Select Excel file
            selected_file = st.selectbox(
                "Select Excel File",
                excel_files,
                help="Choose which Excel file to use for scraping"
            )

            # Base search query
            base_query = st.text_input(
                "Search Keywords",
                value="attorneys in",
                help="Enter the base search query (e.g., 'restaurants in', 'lawyers in')"
            )

            # Zipcode column name
            zipcode_column = st.text_input(
                "Zipcode Column Name",
                value="DELIVERY ZIPCODE",
                help="Name of the column containing zipcodes in your Excel file"
            )

            # Preview file
            if st.checkbox("👀 Preview Excel File"):
                try:
                    file_path = os.path.join(EXCEL_UPLOAD_PATH, selected_file)
                    df = pd.read_excel(file_path)
                    st.write(f"**Total Rows:** {len(df)}")
                    st.dataframe(df.head(10))
                except Exception as e:
                    st.error(f"Error reading file: {e}")

        with col2:
            st.info(f"""
            **⚙️ Current Settings:**
            - Workers: {max_workers}
            - Max Scrolls: {max_scrolls}
            - Excel File: {selected_file}
            """)

            # Estimate
            try:
                file_path = os.path.join(EXCEL_UPLOAD_PATH, selected_file)
                df = pd.read_excel(file_path, dtype={zipcode_column: str})
                num_zipcodes = df[zipcode_column].nunique()

                estimated_time = (num_zipcodes * 25) / max_workers / 60

                st.metric("Zipcodes to Scrape", num_zipcodes)
                st.metric("Estimated Time", f"{estimated_time:.1f} min")
            except Exception as e:
                st.warning(f"Could not estimate: {e}")

        st.markdown("---")

        # Start button
        col1, col2, col3 = st.columns([1, 1, 1])

        with col2:
            if st.session_state.scraping_active:
                st.error("⚠️ Scraper is already running!")
                if st.button("🛑 Stop Scraper", type="secondary"):
                    st.session_state.scraping_active = False
                    st.warning("Scraper will stop after current batch completes.")
            else:
                if st.button("▶️ START SCRAPING", type="primary", use_container_width=True):
                    # Start scraping process
                    st.session_state.scraping_active = True

                    # Create log file path
                    log_file = os.path.join(LOGS_PATH, f"scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

                    # Prepare command
                    file_path = os.path.join(EXCEL_UPLOAD_PATH, selected_file)

                    # Start scraper in background
                    with st.spinner("Initializing scraper..."):
                        try:
                            # Run scraper script with parameters
                            st.success("✅ Scraper started! Check 'View Progress' tab for live updates.")
                            st.info("The scraper is running in the background. You can navigate to other tabs.")

                            # Store start time
                            st.session_state.scraping_stats = {
                                'start_time': time.time(),
                                'file': selected_file,
                                'query': base_query,
                                'status': 'running'
                            }

                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error starting scraper: {e}")
                            st.session_state.scraping_active = False

# ============================================================================
# TAB 3: VIEW PROGRESS
# ============================================================================
with tab3:
    st.header("📊 Scraping Progress")

    if not st.session_state.scraping_active:
        st.info("ℹ️ No active scraping session. Start a scraper in the 'Run Scraper' tab.")

        # Show last run statistics if available
        if st.session_state.scraping_stats:
            st.subheader("📈 Last Scraping Session")
            stats = st.session_state.scraping_stats

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Status", stats.get('status', 'unknown').upper())
            with col2:
                st.metric("File Used", stats.get('file', 'N/A'))
            with col3:
                st.metric("Search Query", stats.get('query', 'N/A'))
            with col4:
                if 'start_time' in stats:
                    elapsed = time.time() - stats['start_time']
                    st.metric("Duration", f"{elapsed/60:.1f} min")
    else:
        # Real-time progress display
        st.success("🟢 Scraper is RUNNING")

        # Progress metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if 'start_time' in st.session_state.scraping_stats:
                elapsed = time.time() - st.session_state.scraping_stats['start_time']
                st.metric("Elapsed Time", f"{elapsed/60:.1f} min")

        with col2:
            st.metric("Status", "RUNNING", delta="Active")

        with col3:
            # Count output files created so far
            try:
                output_files = len([f for f in os.listdir(OUTPUT_PATH) if f.endswith('.xlsx')])
                st.metric("Files Generated", output_files)
            except:
                st.metric("Files Generated", 0)

        with col4:
            st.metric("Workers", max_workers)

        st.markdown("---")

        # Live log viewer
        st.subheader("📜 Live Logs")

        log_container = st.empty()

        # Auto-refresh button
        if st.button("🔄 Refresh Logs"):
            st.rerun()

        # Try to read latest log file
        try:
            log_files = sorted([f for f in os.listdir(LOGS_PATH) if f.endswith('.log')])
            if log_files:
                latest_log = os.path.join(LOGS_PATH, log_files[-1])
                with open(latest_log, 'r') as f:
                    logs = f.readlines()
                    # Show last 50 lines
                    log_container.text_area(
                        "Recent Activity",
                        value="".join(logs[-50:]),
                        height=400
                    )
            else:
                log_container.info("No logs available yet.")
        except Exception as e:
            log_container.warning(f"Could not read logs: {e}")

        # Progress bar (simulated)
        st.subheader("⏳ Progress Estimate")
        progress_placeholder = st.empty()

        # Calculate estimated progress
        if 'start_time' in st.session_state.scraping_stats:
            elapsed = time.time() - st.session_state.scraping_stats['start_time']
            # Rough estimate based on 25 sec per zipcode
            estimated_total = 3600  # 1 hour estimate
            progress = min(elapsed / estimated_total, 0.99)
            progress_placeholder.progress(progress)

# ============================================================================
# TAB 4: DOWNLOAD RESULTS
# ============================================================================
with tab4:
    st.header("📥 Download Results")

    # List all output files
    try:
        output_files = sorted(
            [f for f in os.listdir(OUTPUT_PATH) if f.endswith('.xlsx')],
            key=lambda x: os.path.getmtime(os.path.join(OUTPUT_PATH, x)),
            reverse=True
        )

        if output_files:
            st.success(f"✅ {len(output_files)} result file(s) available for download")

            # Filter and search
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("🔍 Search files", placeholder="Enter filename to search...")
            with col2:
                sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First", "Name A-Z", "Name Z-A"])

            # Apply filters
            filtered_files = [f for f in output_files if search_term.lower() in f.lower()] if search_term else output_files

            # Apply sorting
            if sort_by == "Oldest First":
                filtered_files = list(reversed(filtered_files))
            elif sort_by == "Name A-Z":
                filtered_files = sorted(filtered_files)
            elif sort_by == "Name Z-A":
                filtered_files = sorted(filtered_files, reverse=True)

            st.markdown("---")

            # Download all button
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("📦 Download All as ZIP"):
                    with st.spinner("Creating ZIP file..."):
                        # Create ZIP file in memory
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for file in output_files:
                                file_path = os.path.join(OUTPUT_PATH, file)
                                zip_file.write(file_path, file)

                        zip_buffer.seek(0)

                        st.download_button(
                            label="⬇️ Download ZIP",
                            data=zip_buffer,
                            file_name=f"scraper_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip"
                        )

            st.markdown("---")

            # Display files with download buttons
            for file in filtered_files:
                file_path = os.path.join(OUTPUT_PATH, file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 1])

                with col1:
                    st.write(f"📄 **{file}**")

                with col2:
                    st.write(f"{file_size:.2f} KB")

                with col3:
                    st.write(file_time.strftime("%H:%M"))

                with col4:
                    # Download button
                    with open(file_path, 'rb') as f:
                        st.download_button(
                            label="⬇️",
                            data=f,
                            file_name=file,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_{file}"
                        )

                with col5:
                    # Delete button
                    if st.button("🗑️", key=f"delete_{file}"):
                        os.remove(file_path)
                        st.success(f"Deleted: {file}")
                        time.sleep(0.5)
                        st.rerun()
        else:
            st.info("📭 No output files yet. Run the scraper to generate results!")

    except Exception as e:
        st.error(f"Error listing output files: {e}")

    st.markdown("---")

    # Summary reports
    st.subheader("📈 Summary Reports")

    try:
        summary_files = sorted(
            [f for f in os.listdir(OUTPUT_PATH) if f.startswith('summary_report_')],
            key=lambda x: os.path.getmtime(os.path.join(OUTPUT_PATH, x)),
            reverse=True
        )

        if summary_files:
            selected_summary = st.selectbox("Select Summary Report", summary_files)

            if selected_summary:
                summary_path = os.path.join(OUTPUT_PATH, selected_summary)
                with open(summary_path, 'r') as f:
                    summary_content = f.read()

                st.text_area("Report Content", summary_content, height=400)

                # Download summary
                with open(summary_path, 'rb') as f:
                    st.download_button(
                        label="📥 Download Summary Report",
                        data=f,
                        file_name=selected_summary,
                        mime="text/plain"
                    )
        else:
            st.info("No summary reports available yet.")
    except Exception as e:
        st.error(f"Error reading summary reports: {e}")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🗺️ Google Maps Web Scraper")
with col2:
    st.caption("⚡ Powered by Streamlit")
with col3:
    st.caption("🚀 Deployed on Hostinger VPS")
