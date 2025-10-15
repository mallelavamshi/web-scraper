#!/usr/bin/env python3
"""
Fully Integrated Streamlit UI for Google Maps Web Scraper
Correctly imports from scrape_zip_optimized.py
"""

import streamlit as st
import pandas as pd
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
import zipfile
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add app directory to path
sys.path.insert(0, '/app')

# Import scraper functions from scrape_zip_optimized
try:
    import scrape_zip_optimized as scraper
except ImportError:
    st.error("❌ Error: Could not import scraper module. Check if scrape_zip_optimized.py exists.")
    st.stop()

# Configure page
st.set_page_config(
    page_title="Google Maps Web Scraper",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
EXCEL_PATH = "/app/excel_files"
OUTPUT_PATH = "/app/output"
LOGS_PATH = "/app/logs"

# Create directories
for path in [EXCEL_PATH, OUTPUT_PATH, LOGS_PATH]:
    os.makedirs(path, exist_ok=True)

# Session state initialization
if 'scraping_active' not in st.session_state:
    st.session_state.scraping_active = False
if 'scraping_results' not in st.session_state:
    st.session_state.scraping_results = []
if 'scraping_stats' not in st.session_state:
    st.session_state.scraping_stats = {
        'total': 0,
        'completed': 0,
        'successful': 0,
        'failed': 0,
        'start_time': None
    }

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
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
st.markdown('<div class="main-header">🗺️ Google Maps Web Scraper</div>', unsafe_allow_html=True)
st.markdown("**Real-time Scraping with Live Progress Tracking**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.title("⚙️ System Status")

    if st.session_state.scraping_active:
        st.success("🟢 **SCRAPING ACTIVE**")
    else:
        st.info("⚪ **IDLE**")

    st.markdown("---")

    # File counts
    try:
        excel_count = len([f for f in os.listdir(EXCEL_PATH) if f.endswith('.xlsx')])
        output_count = len([f for f in os.listdir(OUTPUT_PATH) if f.endswith('.xlsx')])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("📤 Inputs", excel_count)
        with col2:
            st.metric("📥 Outputs", output_count)
    except:
        st.metric("📤 Inputs", 0)
        st.metric("📥 Outputs", 0)

    st.markdown("---")

    # Scraping stats
    if st.session_state.scraping_active or st.session_state.scraping_stats['total'] > 0:
        st.subheader("📊 Progress")
        stats = st.session_state.scraping_stats

        if stats['total'] > 0:
            progress = stats['completed'] / stats['total']
            st.progress(progress)
            st.write(f"**{stats['completed']}/{stats['total']}** zipcodes")
            st.write(f"✅ Success: {stats['successful']}")
            st.write(f"❌ Failed: {stats['failed']}")

            if stats['start_time']:
                elapsed = time.time() - stats['start_time']
                st.write(f"⏱️ Time: {elapsed/60:.1f} min")

                if stats['completed'] > 0 and st.session_state.scraping_active:
                    avg_time = elapsed / stats['completed']
                    remaining = (stats['total'] - stats['completed']) * avg_time / 60
                    st.write(f"⏳ Remaining: ~{remaining:.0f} min")

    st.markdown("---")
    st.caption("Built with Streamlit 🎈")
    st.caption("Powered by Selenium + Chrome")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "🚀 Run", "📊 Progress", "📥 Download"])

# ============================================================================
# TAB 1: UPLOAD FILES
# ============================================================================
with tab1:
    st.header("📤 Upload Excel Files")

    uploaded_files = st.file_uploader(
        "Choose Excel files (.xlsx)",
        type=['xlsx'],
        accept_multiple_files=True,
        help="Upload Excel files containing zipcodes"
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) selected")

        # Preview files
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name} ({uploaded_file.size/1024:.2f} KB)"):
                try:
                    df = pd.read_excel(uploaded_file)
                    st.write(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")
                    st.write("**Column Names:**", ", ".join(df.columns.tolist()))
                    st.dataframe(df.head(5))
                except Exception as e:
                    st.error(f"Error reading file: {e}")

        if st.button("💾 Save Files to Server", type="primary"):
            progress_bar = st.progress(0)
            status = st.empty()

            for idx, uploaded_file in enumerate(uploaded_files):
                try:
                    file_path = os.path.join(EXCEL_PATH, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    status.text(f"Saved: {uploaded_file.name}")
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                except Exception as e:
                    st.error(f"Error saving {uploaded_file.name}: {e}")

            status.empty()
            progress_bar.empty()
            st.success("✅ All files saved successfully!")
            time.sleep(1)
            st.rerun()

    st.markdown("---")
    st.subheader("📂 Uploaded Files on Server")

    try:
        excel_files = [f for f in os.listdir(EXCEL_PATH) if f.endswith('.xlsx')]

        if excel_files:
            for file in excel_files:
                col1, col2, col3 = st.columns([4, 1, 1])

                file_path = os.path.join(EXCEL_PATH, file)
                file_size = os.path.getsize(file_path) / 1024

                with col1:
                    st.write(f"📄 **{file}**")
                with col2:
                    st.write(f"{file_size:.2f} KB")
                with col3:
                    if st.button("🗑️", key=f"del_{file}"):
                        os.remove(file_path)
                        st.rerun()
        else:
            st.info("No files uploaded yet. Upload Excel files above to get started.")
    except Exception as e:
        st.error(f"Error listing files: {e}")

# ============================================================================
# TAB 2: RUN SCRAPER
# ============================================================================

def run_scraper_thread(selected_file, base_query, zipcode_column, max_workers, max_scrolls):
    """Background thread that executes the scraper"""
    try:
        # Read Excel file
        file_path = os.path.join(EXCEL_PATH, selected_file)
        df = pd.read_excel(file_path, dtype={zipcode_column: str})

        # Clean and prepare zipcodes
        df[zipcode_column] = df[zipcode_column].astype(str).str.zfill(5)
        zipcodes = df[zipcode_column].unique().tolist()

        # Initialize stats
        st.session_state.scraping_stats = {
            'total': len(zipcodes),
            'completed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': time.time()
        }
        st.session_state.scraping_results = []

        # Run scraper using ThreadPoolExecutor (from scrape_zip_optimized.py)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    scraper.scrape_zipcode,
                    zipcode,
                    base_query,
                    OUTPUT_PATH,
                    i % max_workers
                ): zipcode
                for i, zipcode in enumerate(zipcodes)
            }

            for future in as_completed(futures):
                zipcode = futures[future]
                try:
                    result = future.result()

                    # Update stats
                    st.session_state.scraping_stats['completed'] += 1

                    if result.get('status') == 'success':
                        st.session_state.scraping_stats['successful'] += 1
                    else:
                        st.session_state.scraping_stats['failed'] += 1

                    # Store result
                    st.session_state.scraping_results.append({
                        'zipcode': zipcode,
                        'status': result.get('status', 'unknown'),
                        'count': result.get('count', 0),
                        'time': result.get('time', 0)
                    })

                except Exception as e:
                    st.session_state.scraping_stats['failed'] += 1
                    st.session_state.scraping_stats['completed'] += 1
                    st.session_state.scraping_results.append({
                        'zipcode': zipcode,
                        'status': 'error',
                        'error': str(e)
                    })

    except Exception as e:
        st.error(f"Scraper error: {e}")
    finally:
        st.session_state.scraping_active = False

with tab2:
    st.header("🚀 Run Web Scraper")

    try:
        excel_files = [f for f in os.listdir(EXCEL_PATH) if f.endswith('.xlsx')]
    except:
        excel_files = []

    if not excel_files:
        st.warning("⚠️ No Excel files found. Please upload files in the 'Upload' tab first.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            selected_file = st.selectbox("📄 Select Excel File", excel_files)

            base_query = st.text_input(
                "🔍 Search Keywords",
                value="attorneys in",
                help="Example: 'restaurants in', 'lawyers in', 'doctors in'"
            )

            zipcode_column = st.text_input(
                "📍 Zipcode Column Name",
                value="DELIVERY ZIPCODE",
                help="Enter the exact column name containing zipcodes in your Excel file"
            )

            col_a, col_b = st.columns(2)
            with col_a:
                max_workers = st.slider(
                    "⚡ Concurrent Workers",
                    min_value=1,
                    max_value=4,
                    value=3,
                    help="Recommended: 3 workers for 4 vCPU system"
                )

            with col_b:
                max_scrolls = st.slider(
                    "📜 Max Scrolls",
                    min_value=5,
                    max_value=20,
                    value=10,
                    help="More scrolls = more results but slower"
                )

            if st.checkbox("👀 Preview Excel File"):
                try:
                    file_path = os.path.join(EXCEL_PATH, selected_file)
                    df = pd.read_excel(file_path)
                    st.dataframe(df.head(10))
                except Exception as e:
                    st.error(f"Error reading file: {e}")

        with col2:
            st.info(f"""
            **⚙️ Configuration:**

            📄 File: `{selected_file}`

            🔍 Query: "{base_query}"

            ⚡ Workers: {max_workers}

            📜 Scrolls: {max_scrolls}
            """)

            # Estimate
            try:
                file_path = os.path.join(EXCEL_PATH, selected_file)
                df = pd.read_excel(file_path, dtype={zipcode_column: str})
                num_zipcodes = df[zipcode_column].nunique()
                estimated_time = (num_zipcodes * 25) / max_workers / 60

                st.metric("📊 Unique Zipcodes", num_zipcodes)
                st.metric("⏱️ Estimated Time", f"{estimated_time:.0f} min")
            except Exception as e:
                st.warning(f"Could not estimate: {e}")

        st.markdown("---")

        # Start/Stop button
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.session_state.scraping_active:
                st.error("⚠️ **Scraper is currently running!**")
                st.info("Check the 'Progress' tab for live updates.")

                if st.button("🛑 FORCE STOP", type="secondary"):
                    st.session_state.scraping_active = False
                    st.warning("Scraper will stop after completing current batch...")
            else:
                if st.button("▶️ START SCRAPING", type="primary", use_container_width=True):
                    # Validate inputs
                    try:
                        file_path = os.path.join(EXCEL_PATH, selected_file)
                        test_df = pd.read_excel(file_path)

                        if zipcode_column not in test_df.columns:
                            st.error(f"❌ Column '{zipcode_column}' not found in Excel file!")
                            st.write("Available columns:", ", ".join(test_df.columns.tolist()))
                        else:
                            # Start scraping
                            st.session_state.scraping_active = True

                            # Launch background thread
                            scraper_thread = threading.Thread(
                                target=run_scraper_thread,
                                args=(selected_file, base_query, zipcode_column, max_workers, max_scrolls),
                                daemon=True
                            )
                            scraper_thread.start()

                            st.success("✅ Scraper started successfully!")
                            st.info("Switch to the 'Progress' tab to monitor real-time updates.")
                            time.sleep(2)
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error starting scraper: {e}")

# ============================================================================
# TAB 3: LIVE PROGRESS
# ============================================================================
with tab3:
    st.header("📊 Live Scraping Progress")

    if not st.session_state.scraping_active and st.session_state.scraping_stats['total'] == 0:
        st.info("ℹ️ No scraping session active. Start a scraper in the 'Run' tab.")
    else:
        # Status indicator
        if st.session_state.scraping_active:
            st.success("🟢 **SCRAPING IN PROGRESS**")
        else:
            st.info("✅ **SCRAPING COMPLETED**")

        stats = st.session_state.scraping_stats

        # Progress bar
        if stats['total'] > 0:
            progress = stats['completed'] / stats['total']
            st.progress(progress)

            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("Progress", f"{stats['completed']}/{stats['total']}")
            with col2:
                st.write(f"**{progress*100:.1f}%** complete")

        st.markdown("---")

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("✅ Successful", stats['successful'], delta=None)

        with col2:
            st.metric("❌ Failed", stats['failed'], delta=None)

        with col3:
            if stats['start_time']:
                elapsed = time.time() - stats['start_time']
                st.metric("⏱️ Elapsed", f"{elapsed/60:.1f} min")

        with col4:
            if stats['total'] > 0 and stats['completed'] > 0 and st.session_state.scraping_active:
                avg_time = (time.time() - stats['start_time']) / stats['completed']
                remaining = (stats['total'] - stats['completed']) * avg_time / 60
                st.metric("⏳ Est. Remaining", f"~{remaining:.0f} min")

        st.markdown("---")

        # Recent results
        st.subheader("📋 Recent Activity")

        if st.session_state.scraping_results:
            # Show last 15 results
            recent = st.session_state.scraping_results[-15:]
            recent.reverse()

            for result in recent:
                if result['status'] == 'success':
                    st.success(f"✅ **{result['zipcode']}**: {result['count']} records extracted ({result.get('time', 0):.1f}s)")
                elif result['status'] == 'no_data':
                    st.warning(f"⚠️ **{result['zipcode']}**: No data found")
                else:
                    st.error(f"❌ **{result['zipcode']}**: {result['status']}")
        else:
            st.info("No results yet. Scraping will appear here as it progresses.")

        # Auto-refresh button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Refresh Progress", use_container_width=True):
                st.rerun()

        st.info("💡 **Tip:** This page auto-refreshes every 5 seconds during active scraping.")

# ============================================================================
# TAB 4: DOWNLOAD RESULTS
# ============================================================================
with tab4:
    st.header("📥 Download Results")

    try:
        output_files = sorted(
            [f for f in os.listdir(OUTPUT_PATH) if f.endswith('.xlsx')],
            key=lambda x: os.path.getmtime(os.path.join(OUTPUT_PATH, x)),
            reverse=True
        )

        if output_files:
            st.success(f"✅ **{len(output_files)} result file(s) available for download**")

            # Download all as ZIP
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📦 Download All Files as ZIP", use_container_width=True):
                    with st.spinner("Creating ZIP archive..."):
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for file in output_files:
                                file_path = os.path.join(OUTPUT_PATH, file)
                                zip_file.write(file_path, file)

                        zip_buffer.seek(0)

                        st.download_button(
                            label="⬇️ Click Here to Download ZIP",
                            data=zip_buffer,
                            file_name=f"scraper_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

            st.markdown("---")

            # Individual files
            st.subheader("📄 Individual Files")

            for file in output_files:
                col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 1])

                file_path = os.path.join(OUTPUT_PATH, file)
                file_size = os.path.getsize(file_path) / 1024
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                with col1:
                    st.write(f"📄 {file}")

                with col2:
                    st.write(f"{file_size:.1f} KB")

                with col3:
                    st.write(file_time.strftime("%H:%M"))

                with col4:
                    with open(file_path, 'rb') as f:
                        st.download_button(
                            label="⬇️",
                            data=f,
                            file_name=file,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{file}"
                        )

                with col5:
                    if st.button("🗑️", key=f"del_result_{file}"):
                        os.remove(file_path)
                        st.success(f"Deleted: {file}")
                        time.sleep(0.5)
                        st.rerun()

            # Summary reports
            st.markdown("---")
            st.subheader("📊 Summary Reports")

            summary_files = [f for f in os.listdir(OUTPUT_PATH) if f.startswith('summary_report_')]
            if summary_files:
                selected_summary = st.selectbox("Select Summary Report", summary_files)

                if selected_summary:
                    summary_path = os.path.join(OUTPUT_PATH, selected_summary)
                    with open(summary_path, 'r') as f:
                        summary_content = f.read()

                    st.text_area("Report Content", summary_content, height=300)

                    with open(summary_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download Summary Report",
                            data=f,
                            file_name=selected_summary,
                            mime="text/plain"
                        )
        else:
            st.info("📭 No output files yet. Run the scraper to generate results!")

    except Exception as e:
        st.error(f"Error accessing output files: {e}")

# Auto-refresh during active scraping
if st.session_state.scraping_active:
    time.sleep(5)
    st.rerun()

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🗺️ Google Maps Web Scraper")
with col2:
    st.caption("⚡ Multi-threaded with Real-time Updates")
with col3:
    st.caption("🚀 Powered by Selenium + Streamlit")
