import streamlit as st
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas
from io import BytesIO

# --- 1. 頁面設定 ---
st.set_page_config(page_title="單機版去背神器 (疊加版)", layout="wide")
st.title("🎨 Vibe Coding: 紅框與綠筆同時存在 (本地端)")

# --- 2. 上傳圖片 ---
uploaded_file = st.file_uploader("請上傳圖片 (JPG/PNG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 讀取原始圖片
    original_image = Image.open(uploaded_file).convert("RGBA")
    orig_w, orig_h = original_image.size

    # --- 製作顯示用的縮圖 ---
    display_width = 800
    if orig_w > display_width:
        scale_factor = orig_w / display_width
        display_height = int(orig_h / scale_factor)
        display_image = original_image.resize((display_width, display_height))
    else:
        scale_factor = 1.0
        display_height = orig_h
        display_image = original_image
    
    # 轉成 RGB 避免顯示問題
    canvas_bg = display_image.convert("RGB")

    # --- 3. 介面佈局 ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. 操作區")
        # 選擇工具
        tool_mode = st.radio("選擇工具：", ("🟥 紅框 (挖除)", "🟩 綠筆 (塗抹救回)"), horizontal=True)
        
        # --- 參數設定 ---
        # 這裡的邏輯是：切換工具只改變「畫筆」，不重置「畫布」
        if tool_mode == "🟥 紅框 (挖除)":
            drawing_mode = "rect"       # 矩形模式
            stroke_color = "#ff0000"    # 紅色 (固定這個顏色代碼)
            fill_color = "rgba(255, 0, 0, 0.3)" 
            stroke_width = 2
        else:
            drawing_mode = "freedraw"   # 自由塗抹模式
            stroke_color = "#00ff00"    # 綠色 (固定這個顏色代碼)
            fill_color = "rgba(0, 255, 0, 0.3)" 
            stroke_width = st.slider("🖌️ 調整綠筆粗細", 1, 50, 15)

        # 建立畫布
        canvas_result = st_canvas(
            fill_color=fill_color,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_image=canvas_bg,
            update_streamlit=True,
            height=display_height,
            width=display_width,
            drawing_mode=drawing_mode,
            # === 關鍵修改 ===
            # 使用固定的 Key，這樣切換工具時，原本畫的東西「不會消失」！
            key="canvas_fixed_overlay", 
        )

    with col2:
        st.subheader("2. 結果預覽")

        # --- 4. 核心運算 (顏色判斷法) ---
        if canvas_result.image_data is not None:
            # 取得畫布資料 (這是縮圖尺寸)
            mask_data = canvas_result.image_data
            
            # 轉成圖片物件
            mask_image = Image.fromarray(mask_data.astype('uint8'), mode="RGBA")

            # 放大回原始尺寸 (使用 Nearest 保持邊緣清晰)
            full_mask = mask_image.resize((orig_w, orig_h), resample=Image.NEAREST)
            full_mask_array = np.array(full_mask)

            # 準備原始圖片陣列
            img_array = np.array(original_image)

            # === 智慧判斷邏輯 ===
            # 我們不看現在是什麼工具，我們看「畫布上有什麼顏色」
            
            # 1. 找出所有紅色的像素 (R>0, G=0) -> 把它們挖空
            is_red = (full_mask_array[:, :, 0] > 0) & (full_mask_array[:, :, 1] == 0)
            img_array[is_red, 3] = 0

            # 2. 找出所有綠色的像素 (G>0) -> 把它們救回 (且綠色權重較高，可覆蓋紅色)
            is_green = (full_mask_array[:, :, 1] > 0)
            img_array[is_green, 3] = 255

            # 顯示與下載
            final_image = Image.fromarray(img_array)
            st.image(final_image, caption=f"最終尺寸: {orig_w}x{orig_h}", use_column_width=True)

            buf = BytesIO()
            final_image.save(buf, format="PNG")
            byte_im = buf.getvalue()
            st.download_button("📥 下載成品 PNG", byte_im, "final_overlay.png", "image/png")

        else:
            st.info("👈 請在左側開始操作")
