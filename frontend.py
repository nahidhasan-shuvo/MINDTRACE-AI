import os
import requests
import streamlit as st
from pathlib import Path

# =========================================================
# MINDTRACE AI — NEXT-GEN MULTIMODAL AUTISM SCREENING
# University Research & Clinical Presentation Platform
# =========================================================

st.set_page_config(
    page_title="MINDTRACE AI | Next-Gen Screening Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed", # ক্লিন লুকের জন্য সাইডবার ডিফল্ট কোলাপ্সড
)

API_URL = os.getenv("MINDTRACE_API_URL", "http://127.0.0.1:8000").rstrip("/")

# ------------------------- ULTRA-MODERN CSS ----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #0f172a;
}

/* Background Aurora Mesh Effect */
.stApp {
    background: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.12) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(139, 92, 246, 0.08) 0px, transparent 50%),
        #f8fafc;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 5rem;
    max-width: 1250px;
}

/* Top Floating Navigation */
.nav-container {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 24px;
    padding: 14px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 25px -4px rgba(0, 0, 0, 0.04);
    margin-bottom: 28px;
}

.brand-text {
    font-size: 20px;
    font-weight: 900;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #1e1b4b 0%, #4338ca 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Modern Hero Section */
.hero-wrapper {
    background: linear-gradient(145deg, #1e1b4b 0%, #312e81 40%, #4338ca 100%);
    border-radius: 32px;
    padding: 50px 48px;
    color: white;
    margin-bottom: 35px;
    box-shadow: 0 25px 60px -18px rgba(67, 56, 202, 0.35);
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

.hero-badge {
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    color: #e0e7ff;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 18px;
}

.hero-title {
    font-size: 44px;
    font-weight: 900;
    line-height: 1.15;
    letter-spacing: -0.03em;
    margin-bottom: 16px;
    color: #ffffff;
}

/* Premium Cards */
.glass-card {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 24px;
    padding: 26px;
    box-shadow: 0 10px 30px -10px rgba(15, 23, 42, 0.04);
    transition: all 0.25s ease;
}

.glass-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 20px 40px -12px rgba(15, 23, 42, 0.08);
    border-color: #cbd5e1;
}

/* Prediction Result Cards */
.result-card-autistic {
    background: linear-gradient(145deg, #fff5f5 0%, #ffffff 100%);
    border: 2px solid #fecdd3;
    border-radius: 28px;
    padding: 38px;
    box-shadow: 0 25px 60px -15px rgba(225, 29, 72, 0.18);
}

.result-card-control {
    background: linear-gradient(145deg, #f0fdf4 0%, #ffffff 100%);
    border: 2px solid #bbf7d0;
    border-radius: 28px;
    padding: 38px;
    box-shadow: 0 25px 60px -15px rgba(22, 163, 74, 0.18);
}

/* Primary Action Button */
.stButton > button {
    background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%) !important;
    color: white !important;
    font-size: 16px !important;
    font-weight: 800 !important;
    padding: 16px 36px !important;
    border-radius: 18px !important;
    border: none !important;
    box-shadow: 0 12px 28px -6px rgba(79, 70, 229, 0.45) !important;
    transition: all 0.25s ease !important;
    letter-spacing: -0.01em;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 18px 36px -6px rgba(79, 70, 229, 0.6) !important;
}

/* Clean Custom File Upload Boxes */
[data-testid="stFileUploader"] {
    background: #f8fafc;
    border: 2px dashed #cbd5e1;
    border-radius: 18px;
    padding: 14px;
    transition: all 0.2s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: #6366f1;
    background: #f1f5f9;
}
</style>
""", unsafe_allow_html=True)


# ------------------------- BACKEND FUNCTIONS ------------------------

def check_backend():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        if response.ok:
            return True, response.json()
        return False, {}
    except requests.RequestException:
        return False, {}


def show_presentation_result(raw_data):
    """উচ্চমানের এক্সিকিউটিভ ডায়াগনস্টিক রিপোর্ট ভিউ"""
    res = raw_data.get("result", raw_data)
    if not isinstance(res, dict):
        st.error("সার্ভার রেসপন্স পার্স করতে সমস্যা হয়েছে।")
        return

    predicted_class = res.get("predicted_class", "Unknown")
    confidence = float(res.get("confidence", 0.0))
    control_prob = float(res.get("control_probability", 0.0))
    autistic_prob = float(res.get("autistic_probability", 0.0))

    is_autistic = predicted_class.lower() == "autistic"

    card_class = "result-card-autistic" if is_autistic else "result-card-control"
    theme_color = "#e11d48" if is_autistic else "#16a34a"
    theme_bg = "#ffe4e6" if is_autistic else "#dcfce7"
    badge_label = "AUTISTIC SPECTRUM INDICATOR" if is_autistic else "TYPICAL (CONTROL) DEVELOPMENT"
    icon = "🧩" if is_autistic else "🌱"

    st.markdown(f"""
    <div class="{card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
            <div>
                <span style="background:{theme_bg}; color:{theme_color}; padding:6px 14px; border-radius:10px; font-weight:800; font-size:12px; letter-spacing:0.06em; text-transform:uppercase; font-family:'JetBrains Mono';">
                    ● CONSENSUS CLASSIFICATION
                </span>
                <h1 style="font-size:36px; font-weight:900; color:#0f172a; margin:14px 0 6px 0; letter-spacing:-0.03em;">
                    {icon} {badge_label}
                </h1>
                <p style="color:#64748b; font-size:15px; margin:0; max-width:620px; line-height:1.5;">
                    ড্রয়িং (ResNet-18), ভয়েস স্পেকট্রাম (2D-CNN) এবং শারীরিক গতিবিধি (3D-CNN)—এই তিনটি স্বাধীন নিউরাল ফিচার ফিউশন করে মডেল এই চূড়ান্ত সিদ্ধান্ত গ্রহণ করেছে।
                </p>
            </div>
            <div style="text-align: right; background: white; padding: 18px 28px; border-radius: 20px; border: 1px solid rgba(226, 232, 240, 0.8); box-shadow: 0 10px 25px -5px rgba(0,0,0,0.03);">
                <div style="font-size:11px; font-weight:800; color:#94a3b8; text-transform:uppercase; letter-spacing:0.08em;">
                    Confidence Score
                </div>
                <div style="font-size:46px; font-weight:900; color:{theme_color}; font-family:'JetBrains Mono'; line-height:1.1;">
                    {confidence:.2f}%
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # ডুয়েল প্রোবাবিলিটি মিটার
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"""
        <div class="glass-card" style="border-left: 6px solid #22c55e;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-weight:800; font-size:16px; color:#1e293b;">🌱 Typical / Control Score</span>
                <span style="font-family:'JetBrains Mono'; font-weight:800; font-size:18px; color:#16a34a;">{control_prob:.2f}%</span>
            </div>
            <p style="font-size:13px; color:#64748b; margin-bottom:12px;">স্বাভাবিক আচরণ ও চারিত্রিক বৈশিষ্ট্যের মাত্রা</p>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(max(control_prob / 100.0, 0.0), 1.0))

    with m2:
        st.markdown(f"""
        <div class="glass-card" style="border-left: 6px solid #f43f5e;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-weight:800; font-size:16px; color:#1e293b;">🧩 Autistic Spectrum Score</span>
                <span style="font-family:'JetBrains Mono'; font-weight:800; font-size:18px; color:#e11d48;">{autistic_prob:.2f}%</span>
            </div>
            <p style="font-size:13px; color:#64748b; margin-bottom:12px;">অটিজম স্পেকট্রাম সংশ্লিষ্ট বৈশিষ্ট্যের সম্ভাবনা</p>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(max(autistic_prob / 100.0, 0.0), 1.0))

    # ৩টি পাইপলাইনের টেকনিক্যাল সামারি (শিক্ষকদের জন্য)
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    with st.expander("🎓 প্রেজেন্টেশন টেকনিক্যাল মেট্রিক্স ও মাল্টিমোডাল ব্রেকডাউন", expanded=True):
        st.markdown("""
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:16px; margin-top:8px;">
            <div style="background:#f8fafc; padding:18px; border-radius:18px; border:1px solid #e2e8f0;">
                <div style="font-size:11px; font-weight:800; color:#6366f1; text-transform:uppercase;">🖼️ Image Pipeline</div>
                <div style="font-weight:800; color:#0f172a; margin-top:4px; font-size:16px;">ResNet-18 Deep Backbone</div>
                <div style="font-size:12px; color:#64748b; margin-top:2px;">512-D Latent Representation</div>
            </div>
            <div style="background:#f8fafc; padding:18px; border-radius:18px; border:1px solid #e2e8f0;">
                <div style="font-size:11px; font-weight:800; color:#06b6d4; text-transform:uppercase;">🎙️ Audio Pipeline</div>
                <div style="font-weight:800; color:#0f172a; margin-top:4px; font-size:16px;">40-MFCC + 2D-CNN</div>
                <div style="font-size:12px; color:#64748b; margin-top:2px;">Acoustic Prosody & Pitch Variance</div>
            </div>
            <div style="background:#f8fafc; padding:18px; border-radius:18px; border:1px solid #e2e8f0;">
                <div style="font-size:11px; font-weight:800; color:#8b5cf6; text-transform:uppercase;">🎬 Action Pipeline</div>
                <div style="font-weight:800; color:#0f172a; margin-top:4px; font-size:16px;">3D-CNN Spatio-Temporal</div>
                <div style="font-size:12px; color:#64748b; margin-top:2px;">8-Frame Kinematic Motor Vector</div>
            </div>
            <div style="background:#f8fafc; padding:18px; border-radius:18px; border:1px solid #e2e8f0;">
                <div style="font-size:11px; font-weight:800; color:#10b981; text-transform:uppercase;">⚖️ Fusion Method</div>
                <div style="font-weight:800; color:#0f172a; margin-top:4px; font-size:16px;">Equal Late Fusion</div>
                <div style="font-size:12px; color:#64748b; margin-top:2px;">Decision Threshold (τ = 0.50)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ------------------------- TOP NAVIGATION BAR ------------------------

backend_ok, info = check_backend()
status_badge = (
    '<span style="background:#dcfce7; color:#15803d; padding:4px 12px; border-radius:999px; font-size:11px; font-weight:800;">🟢 API Engine Active (Port 8000)</span>'
    if backend_ok else
    '<span style="background:#fee2e2; color:#b91c1c; padding:4px 12px; border-radius:999px; font-size:11px; font-weight:800;">🔴 Backend Offline</span>'
)

st.markdown(f"""
<div class="nav-container">
    <div class="brand-text">
        🧠 MINDTRACE <span style="color:#6366f1;">AI</span>
    </div>
    <div>
        {status_badge}
    </div>
</div>
""", unsafe_allow_html=True)

# আধুনিক সেগমেন্টেড ট্যাব ন্যাভিগেশন
tab_home, tab_screening, tab_science, tab_benchmarks, tab_team = st.tabs([
    "🏠 হোম ও পরিচিতি",
    "🔬 AI স্ক্রীনিং স্টুডিও",
    "🧬 ট্রাই-মোডাল বিজ্ঞান",
    "📊 পারফরম্যান্স ও মেট্রিক্স",
    "👥 রিসার্চ টিম ও যোগাযোগ"
])


# =====================================================================
# TAB 1: HOME & HERO
# =====================================================================
with tab_home:

    st.markdown("""
    <div class="hero-wrapper">
        <span class="hero-badge">🎓 University Thesis & Clinical AI Prototype</span>
        <h1 class="hero-title">Early Autism Spectrum Screening<br>Through Tri-Modal Deep Learning</h1>
        <p style="font-size:16px; opacity:0.92; max-width:800px; line-height:1.6; margin-bottom:24px; color:#e0e7ff;">
            একটি সামগ্রিক, নিরপেক্ষ এবং দ্রুত স্ক্রীনিং প্ল্যাটফর্ম। একক কোনো তথ্যের ওপর নির্ভর না করে শিশুর আঁকা ছবি (Drawing), কণ্ঠস্বরের স্বরভঙ্গি (Voice) এবং শারীরিক অঙ্গভঙ্গির ভিডিও (Action) এর সম্মিলিত বিশ্লেষণ।
        </p>
    </div>
    """, unsafe_allow_html=True)

    # স্ট্যাটাস গ্রিড
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:32px; font-weight:900; color:#4338ca;">3</div>
            <div style="font-size:12px; font-weight:800; color:#64748b; text-transform:uppercase;">Modalities</div>
            <div style="font-size:11px; color:#94a3b8; margin-top:2px;">Drawing, Voice & Video</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:32px; font-weight:900; color:#06b6d4;">Late Fusion</div>
            <div style="font-size:12px; font-weight:800; color:#64748b; text-transform:uppercase;">Consensus Engine</div>
            <div style="font-size:11px; color:#94a3b8; margin-top:2px;">Equal Weighted Logits</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:32px; font-weight:900; color:#10b981;">80 / 20</div>
            <div style="font-size:12px; font-weight:800; color:#64748b; text-transform:uppercase;">Train-Test Split</div>
            <div style="font-size:11px; color:#94a3b8; margin-top:2px;">Unseen Test Verified</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:32px; font-weight:900; color:#f43f5e;">Zero-PII</div>
            <div style="font-size:12px; font-weight:800; color:#64748b; text-transform:uppercase;">Privacy Core</div>
            <div style="font-size:11px; color:#94a3b8; margin-top:2px;">In-Memory Processing</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("### 🧬 প্রজেক্ট ব্যাকগ্রাউন্ড ও ক্লিনিক্যাল মোটিভেশন")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0 0 8px 0; color:#1e293b; font-weight:800;">⚠️ সনাতন ডায়াগনস্টিক চ্যালেঞ্জ</h4>
            <p style="font-size:14px; color:#64748b; line-height:1.6; margin:0;">
                প্রচলিত অটিজম স্ক্রীনিংয়ে ম্যানুয়াল প্রশ্নাবলী (যেমন M-CHAT) এবং দীর্ঘস্থায়ী পর্যবেক্ষণের প্রয়োজন হয়। বিশেষজ্ঞ চিকিৎসকের স্বল্পতার কারণে প্রাথমিক পর্যায়ে (Golden Window of 2-4 years) সঠিক ইন্টারভেনশন পেতে প্রায়ই ৩ থেকে ৫ বছর দেরি হয়ে যায়।
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_r:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0 0 8px 0; color:#1e293b; font-weight:800;">💡 আমাদের এআই চালিত সমাধান</h4>
            <p style="font-size:14px; color:#64748b; line-height:1.6; margin:0;">
                MINDTRACE AI কৃত্রিম বুদ্ধিমত্তার মাধ্যমে ফাইন-মোটর ড্রয়িং, ভোকাল পিচ অসামঞ্জস্যতা এবং শারীরিক মুভমেন্ট প্যাটার্ন একত্রিত করে। এটি চিকিৎসকদের জন্য একটি অবজেক্টিভ ও নিরপেক্ষ সেকেন্ডারি ডিসিশন-সাপোর্ট টুল হিসেবে কাজ করতে সক্ষম।
            </p>
        </div>
        """, unsafe_allow_html=True)


# =====================================================================
# TAB 2: AI SCREENING STUDIO (THE MAIN TOOL)
# =====================================================================
with tab_screening:

    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="font-size:28px; font-weight:900; color:#1e1b4b; margin:0;">🔬 Interactive AI Screening Console</h2>
        <p style="color:#64748b; font-size:14px; margin-top:4px;">
            তিনটি মোডালিটি (ড্রয়িং, অডিও এবং ভিডিও) আপলোড করে ডিপ লার্নিং মডেলের লাইভ প্রেডিকশন যাচাই করুন।
        </p>
    </div>
    """, unsafe_allow_html=True)

    u1, u2, u3 = st.columns(3)

    with u1:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0 0 2px 0; color:#1e293b; font-weight:800;">🖼️ ১. ড্রয়িং / ছবি</h4>
            <p style="font-size:12px; color:#64748b; margin:0 0 10px 0;">শিশুর আঁকা ছবি বা স্থির প্রতিচ্ছবি (ResNet-18)</p>
        </div>
        """, unsafe_allow_html=True)
        image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"], key="mod_img", label_visibility="collapsed")
        if image_file:
            st.image(image_file, use_container_width=True)

    with u2:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0 0 2px 0; color:#1e293b; font-weight:800;">🎙️ ২. কণ্ঠস্বর / অডিও</h4>
            <p style="font-size:12px; color:#64748b; margin:0 0 10px 0;">কথোপকথনের অডিও ক্লিপ (40-MFCC 2D-CNN)</p>
        </div>
        """, unsafe_allow_html=True)
        audio_file = st.file_uploader("Upload Audio", type=["wav", "mp3", "m4a", "ogg"], key="mod_aud", label_visibility="collapsed")
        if audio_file:
            st.audio(audio_file)

    with u3:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0 0 2px 0; color:#1e293b; font-weight:800;">🎬 ৩. অ্যাকশন / ভিডিও</h4>
            <p style="font-size:12px; color:#64748b; margin:0 0 10px 0;">শারীরিক নড়াচড়া বা আচরণের ক্লিপ (3D-CNN)</p>
        </div>
        """, unsafe_allow_html=True)
        video_file = st.file_uploader("Upload Video", type=["mp4", "mov", "avi"], key="mod_vid", label_visibility="collapsed")
        if video_file:
            st.video(video_file)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    ready = all([image_file, audio_file, video_file])

    if not ready:
        st.info("📥 প্রেডিকশন শুরু করতে অনুগ্রহ করে তিনটি ফাইলই আপলোড করুন।")

    btn_predict = st.button("🚀 Run Deep Multimodal Prediction", use_container_width=True, disabled=not ready)

    if btn_predict:
        files = {
            "image": (image_file.name, image_file.getvalue(), image_file.type or "image/jpeg"),
            "audio": (audio_file.name, audio_file.getvalue(), audio_file.type or "audio/wav"),
            "video": (video_file.name, video_file.getvalue(), video_file.type or "video/mp4"),
        }

        try:
            with st.spinner("🧠 তিনটি স্বাধীন নিউরাল নেটওয়ার্কে লজিট ফিউশন চলছে, অপেক্ষা করুন..."):
                resp = requests.post(f"{API_URL}/predict", files=files, timeout=120)

            if resp.ok:
                result = resp.json()
                show_presentation_result(result)
            else:
                st.error(f"সার্ভার এরর: HTTP {resp.status_code}")
                st.code(resp.text)

        except Exception as exc:
            st.error(f"ব্যাকএন্ড সার্ভারে কানেক্ট করা যায়নি: {exc}")


# =====================================================================
# TAB 3: TRI-MODAL SCIENCE
# =====================================================================
with tab_science:
    st.markdown("### 🧬 ট্রাই-মোডাল বায়োমার্কারের বৈজ্ঞানিক যুক্তি")
    st.caption("ক্লিনিক্যাল পেডিয়াট্রিক্সে কেন এই তিনটি মোডালিটি অপরিহার্য")

    b1, b2, b3 = st.columns(3)
    with b1:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color:#4338ca; font-weight:800;">🎨 Visual Biomarker (Drawing)</h4>
            <p style="font-size:13px; color:#64748b; line-height:1.6;">
                <strong>মেডিকেল তাৎপর্য:</strong> শিশুদের আঁকা ছবির রেখার গভীরতা ও স্ট্রোক প্যাটার্ন তাদের ফাইন-মোটর কন্ট্রোল ও ভিজ্যুও-স্পেশিয়াল প্ল্যানিং নির্দেশ করে।
            </p>
            <p style="font-size:12px; color:#4338ca; font-weight:700;">আর্কিটেকচার: ResNet-18 ImageNet Weights (512-D)</p>
        </div>
        """, unsafe_allow_html=True)
    with b2:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color:#06b6d4; font-weight:800;">🎙️ Acoustic Biomarker (Voice)</h4>
            <p style="font-size:13px; color:#64748b; line-height:1.6;">
                <strong>মেডিকেল তাৎপর্য:</strong> অটিজম স্পেকট্রামে কণ্ঠস্বরের স্বরভঙ্গি (Atypical Prosody), ফ্রিকোয়েন্সি সুইং এবং রেসপন্স প্যাটার্ন সাধারণের তুলনায় ভিন্ন হয়।
            </p>
            <p style="font-size:12px; color:#06b6d4; font-weight:700;">আর্কিটেকচার: 40-MFCCs + 2D CNN (64-D)</p>
        </div>
        """, unsafe_allow_html=True)
    with b3:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color:#8b5cf6; font-weight:800;">🎬 Kinematic Biomarker (Action)</h4>
            <p style="font-size:13px; color:#64748b; line-height:1.6;">
                <strong>মেডিকেল তাৎপর্য:</strong> পুনরাবৃত্তিমূলক আচরণ বা হাত-পায়ের বিশেষ মুভমেন্ট (Motor Stereotypies) ৩D ভিডিও স্পেসের স্প্যাশিও-টেম্পোরাল ফ্রেমে ধরা পড়ে।
            </p>
            <p style="font-size:12px; color:#8b5cf6; font-weight:700;">আর্কিটেকচার: Spatio-Temporal 3D CNN (64-D)</p>
        </div>
        """, unsafe_allow_html=True)


# =====================================================================
# TAB 4: BENCHMARKS & EVALUATION
# =====================================================================
with tab_benchmarks:
    st.markdown("### 📊 টেস্ট ইভ্যালুয়েশন ও পারফরম্যান্স পরিসংখ্যান")
    st.caption("মডেলটি ট্রেইনিংয়ে কখনোই দেখেনি এমন ২০% আনসিন টেস্ট সেটের ওপর ফলাফল")

    metrics_file = Path("results/test_metrics.csv")
    matrix_file = Path("results/test_confusion_matrix.png")
    roc_file = Path("results/test_roc_curve.png")

    bm1, bm2 = st.columns([1, 1.2])
    with bm1:
        if metrics_file.exists():
            import pandas as pd
            df = pd.read_csv(metrics_file)
            st.dataframe(df.T.rename(columns={0: "Score / Count"}), use_container_width=True)
        else:
            st.info("💡 `results/test_metrics.csv` ফাইলটি পাওয়া যায়নি। ট্রেইনিং সম্পন্ন হলে ফাইলটি এখানে সরাসরি শো করবে।")

    with bm2:
        if matrix_file.exists():
            st.image(str(matrix_file), caption="Confusion Matrix (Unseen Test Data)", use_container_width=True)
        if roc_file.exists():
            st.image(str(roc_file), caption="Receiver Operating Characteristic (ROC-AUC)", use_container_width=True)


# =====================================================================
# TAB 5: TEAM & CONTACT
# =====================================================================
with tab_team:
    st.markdown("### 👥 রিসার্চ টিম ও প্রাতিষ্ঠানিক তথ্য")

    tm1, tm2 = st.columns(2)
    with tm1:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0; color:#1e1b4b; font-weight:800;">🎓 গবেষক / থিসিস অথর</h4>
            <p style="font-size:18px; font-weight:800; color:#4338ca; margin:4px 0 0 0;">মোঃ নাহিদ হাসান</p>
            <p style="font-size:13px; color:#64748b; margin-top:2px;">কম্পিউটার সায়েন্স অ্যান্ড ইঞ্জিনিয়ারিং বিভাগ</p>
            <hr style="border-color:#e2e8f0; margin:16px 0;">
            <p style="font-size:13px; color:#64748b; line-height:1.5;">
                <strong>গবেষণার শিরোনাম:</strong> Multimodal Late-Fusion Deep Learning for Early Pediatric Autism Spectrum Disorder Screening
            </p>
        </div>
        """, unsafe_allow_html=True)
    with tm2:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0; color:#1e1b4b; font-weight:800;">📬 প্রাতিষ্ঠানিক যোগাযোগ ও কোলাবোরেশন</h4>
            <p style="font-size:13px; color:#64748b; margin-top:6px; line-height:1.6;">
                একাডেমিক পর্যালোচনা, ডেটাসেট রেফারেন্স বা যৌথ গবেষণার জন্য যোগাযোগ করতে পারেন।
            </p>
            <p style="font-size:13px; color:#1e293b; margin-top:12px;">
                ✉️ <strong>Email:</strong> research@mindtrace.ai<br>
                🌐 <strong>Codebase:</strong> github.com/nahidhasan/Autism_combine
            </p>
        </div>
        """, unsafe_allow_html=True)


# ------------------------- ACADEMIC FOOTER ------------------------
st.markdown("""
<div style="border-top:1px solid #e2e8f0; margin-top:60px; padding-top:25px; text-align:center; color:#94a3b8; font-size:12px;">
    <strong>MINDTRACE AI</strong> — Multimodal Autism Spectrum Research Platform<br>
    Department of Computer Science & Engineering · Academic Presentation Prototype · <em>Strictly for Defense Demonstration</em>
</div>
""", unsafe_allow_html=True)