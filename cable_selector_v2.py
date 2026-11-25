
import streamlit as st

st.set_page_config(
    page_title="ケーブル選定",
    page_icon="🔌",
    layout="centered"
)

st.title("ケーブル選定")

# =====================================
# 許容電流データ
# 添付資料 JCS 0168-2 (2010)
# =====================================

SIZES = [14, 22, 38, 60, 100, 150, 200, 250]

# 空中・暗きょ布設（基底温度40℃）
AIR_2CORE = [91, 120, 165, 225, 310, 400, 490, 565]
AIR_3CORE = [86, 110, 155, 210, 290, 380, 465, 535]

# 管路引入れ布設（2孔1条・基底温度25℃）
FEP_2CORE = [90, 115, 160, 210, 285, 360, 430, 490]
FEP_3CORE = [81, 105, 145, 185, 250, 320, 380, 430]

# =====================================
# 回路方式
# =====================================

CIRCUITS = {
    "三相3線式": {
        "cable": "CVT",
        "cores": 3,
        "coefficient": 30.8,
    },
    "単相3線式": {
        "cable": "CVT",
        "cores": 2,
        "coefficient": 17.8,
    },
    "単相2線式": {
        "cable": "CVD",
        "cores": 2,
        "coefficient": 35.6,
    },
}

# =====================================
# 入力画面
# =====================================

st.subheader("計算条件")

circuit_name = st.selectbox(
    "回路方式",
    list(CIRCUITS.keys())
)

circuit = CIRCUITS[circuit_name]

if circuit_name == "三相3線式":
    voltage_options = ["210V", "440V"]
else:
    voltage_options = ["100V", "210V"]

voltage_label = st.selectbox(
    "電源電圧",
    voltage_options
)

voltage = int(voltage_label.replace("V", ""))

installation = st.selectbox(
    "敷設方式",
    [
        "ケーブルラック",
        "ころがし配線",
        "PFD管",
        "G管",
        "HIVE管",
        "FEP管",
    ]
)

col1, col2 = st.columns(2)

with col1:
    current = st.number_input(
        "ブレーカ容量（A）",
        min_value=0,
        max_value=5000,
        value=100,
        step=1,
        format="%d"
    )

with col2:
    distance = st.number_input(
        "ケーブルこう長（m）",
        min_value=0.1,
        max_value=10000.0,
        value=30.0,
        step=1.0,
        format="%.1f"
    )

st.caption("電圧降下：電源電圧の2％")

# =====================================
# ブレーカ容量の選択
# =====================================

if installation in ("ケーブルラック", "ころがし配線"):

    if circuit["cores"] == 2:
        ampacity_table = AIR_2CORE
    else:
        ampacity_table = AIR_3CORE

else:

    if circuit["cores"] == 2:
        ampacity_table = FEP_2CORE
    else:
        ampacity_table = FEP_3CORE

# =====================================
# ケーブル選定
# =====================================

if st.button(
    "ケーブル選定",
    type="primary",
    use_container_width=True
):

    allowable_drop = voltage * 0.02

    # ブレーカ容量によるサイズ選定
    ampacity_size = None

    for size, ampacity in zip(SIZES, ampacity_table):

        if ampacity >= current:
            ampacity_size = size
            break

    # 単相3線式100Vは電圧降下計算をしない
    skip_drop = (
        circuit_name == "単相3線式"
        and voltage == 100
    )

    voltage_size = None
    required_area = None

    if not skip_drop:

        # 電圧降下による必要断面積
        required_area = (
            circuit["coefficient"]
            * distance
            * current
            / (1000 * allowable_drop)
        )

        for size in SIZES:

            if size >= required_area:
                voltage_size = size
                break

    # =================================
    # 選定結果
    # =================================

    if ampacity_size is None:

        st.error(
            "ブレーカ容量を満足するサイズがありません。"
            "250mm²を超えています。"
        )

    elif not skip_drop and voltage_size is None:

        st.error(
            "電圧降下を満足するサイズがありません。"
            "250mm²を超えています。"
        )

    else:

        if skip_drop:
            selected_size = ampacity_size
        else:
            selected_size = max(
                ampacity_size,
                voltage_size
            )

        index = SIZES.index(selected_size)

        selected_ampacity = ampacity_table[index]

        # =================================
        # 実際の電圧降下・最大こう長
        # =================================

        if not skip_drop:

            actual_drop = (
                circuit["coefficient"]
                * distance
                * current
                / (1000 * selected_size)
            )

            max_distance = (
                selected_size
                * 1000
                * allowable_drop
                / (circuit["coefficient"] * current)
            )

        # =================================
        # 結果表示
        # =================================

        st.divider()

        st.markdown(
            f"""
            <div style="font-size:1.1rem;">
                推奨ケーブル
            </div>
            <div style="
                font-size:2.4rem;
                font-weight:bold;
                line-height:1.4;
            ">
                {circuit["cable"]} {selected_size} mm²
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div style="font-size:0.9rem;">
                許容電流：{selected_ampacity} A
            </div>
            """,
            unsafe_allow_html=True
        )

        if skip_drop:

            st.info(
                "単相3線式100Vは、指定により"
                "電圧降下計算を行っていません。"
            )

        else:

            result1, result2 = st.columns(2)

            with result1:
                st.metric(
                    "実際の電圧降下",
                    f"{actual_drop:.2f} V"
                )

            with result2:
                st.metric(
                    "最大こう長",
                    f"{max_distance:.1f} m"
                )

        # =================================
        # 選定条件
        # =================================

        st.markdown("### 選定条件")

        st.write(f"回路方式：{circuit_name}")
        st.write(f"ケーブル：{circuit['cable']}")
        st.write(f"電源電圧：{voltage_label}")
        st.write(f"敷設方式：{installation}")
        st.write(f"ブレーカ容量：{current:g} A")
        st.write(f"ケーブルこう長：{distance:g} m")

        st.write(
            f"電圧降下：{allowable_drop:.2f} V"
        )

        st.write(
            f"ブレーカ容量による必要サイズ：{ampacity_size} mm²"
        )

        if skip_drop:

            st.write("電圧降下による選定：計算対象外")

        else:

            st.write(
                f"必要断面積：{required_area:.2f} mm²"
            )

            st.write(
                f"電圧降下による必要サイズ：{voltage_size} mm²"
            )

        st.caption(
            "ブレーカ容量と電圧降下の両方を満足する"
            "サイズを選定しています。"
        )

# =====================================
# 注意事項
# =====================================

st.divider()

st.caption(
    "実施設計では周囲温度、布設条数、集合布設、"
    "ケーブルの実際の布設条件などを別途確認してください。"
)
