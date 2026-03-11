import streamlit as st
import os
import json
import shutil
import pandas as pd
from pathlib import Path
from PIL import Image

# --- 配置区 ---
TARGET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'data')
SUPPORTED_EXTENSIONS = {".jsonl", ".json", ".png", ".jpg", ".jpeg", ".gif"}

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

st.set_page_config(page_title="树状文件管理器", layout="wide")

#  1. 缓存：扫描目录结构
@st.cache_data
def get_directory_tree(root_path):
    tree = {"files": [], "subfolders": {}}
    root = Path(root_path)
    try:
        for item in root.iterdir():
            if item.is_dir():
                sub_tree = get_directory_tree(item)
                tree["subfolders"][item.name] = sub_tree
            elif item.is_file():
                tree["files"].append(item.name)
    except Exception as e:
        st.error(f"扫描出错: {e}")
    
    tree["files"].sort()
    return tree

# --- 2. 缓存：文件读取 ---
@st.cache_data
def load_jsonl_cached(file_path, mtime):
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 1000: break 
            data.append(json.loads(line))
    return pd.DataFrame(data)

@st.cache_data
def load_json_cached(file_path, mtime):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame([data])

@st.cache_data
def load_image_cached(file_path, mtime):
    return Image.open(file_path)

#  核心功能：递归渲染 UI 
def render_tree_ui(tree_data, current_path):
    # 1. 先渲染当前层级的子文件夹
    for folder_name, sub_data in tree_data["subfolders"].items():
        # 使用图标和名称作为折叠框标题
        with st.expander(f"📁 {folder_name}", expanded=False):
            full_folder_path = str(current_path / folder_name)
            is_selected_folder = (
                st.session_state.get("selected_path") == full_folder_path
                and st.session_state.get("selected_type") == "folder"
            )
            folder_label = f"📁 {folder_name}" if not is_selected_folder else f"🎯 **{folder_name}**"
            # 【修改点】 use_container_width=True -> width='stretch'
            if st.button(folder_label, key=f"folder::{full_folder_path}", width='stretch'):
                st.session_state.selected_path = full_folder_path
                st.session_state.selected_type = "folder"
                st.rerun()
            # 递归调用
            render_tree_ui(sub_data, current_path / folder_name)
            
    # 2. 再渲染当前层级的文件
    for f_name in tree_data["files"]:
        full_f_path = str(current_path / f_name)
        # 针对选中状态进行加粗显示
        is_selected = (
            st.session_state.get("selected_path") == full_f_path
            and st.session_state.get("selected_type") == "file"
        )
        label = f"📄 {f_name}" if not is_selected else f"🎯 **{f_name}**"
        
        # 【修改点】 use_container_width=True -> width='stretch'
        if st.button(label, key=full_f_path, width='stretch'):
            st.session_state.selected_path = full_f_path
            st.session_state.selected_type = "file"
            st.rerun()

#  删除功能 
def handle_delete_file(full_path):
    try:
        if os.path.exists(full_path) and os.path.isfile(full_path):
            os.remove(full_path)
            st.cache_data.clear()
            st.session_state.selected_path = None
            st.session_state.selected_type = None
            st.toast("文件已永久删除")
            return True
    except Exception as e:
        st.error(f"删除失败: {e}")
    return False

def handle_delete_folder(full_path):
    try:
        if os.path.exists(full_path) and os.path.isdir(full_path):
            shutil.rmtree(full_path)
            st.cache_data.clear()
            st.session_state.selected_path = None
            st.session_state.selected_type = None
            st.toast("文件夹已永久删除")
            return True
    except Exception as e:
        st.error(f"删除失败: {e}")
    return False

def handle_rename_path(old_path, new_name):
    new_name = new_name.strip()
    if not new_name:
        st.error("新名称不能为空")
        return False
    if "/" in new_name or "\\" in new_name:
        st.error("新名称不能包含路径分隔符")
        return False
    try:
        old_path = Path(old_path)
        new_path = old_path.parent / new_name
        if new_path.exists():
            st.error("目标名称已存在")
            return False
        os.rename(old_path, new_path)
        st.cache_data.clear()
        st.session_state.selected_path = str(new_path)
        st.toast("重命名成功")
        return True
    except Exception as e:
        st.error(f"重命名失败: {e}")
    return False

def handle_rename_file(old_path, new_name):
    old_path = Path(old_path)
    old_ext = old_path.suffix
    new_name = new_name.strip()
    if not new_name:
        st.error("新名称不能为空")
        return False
    if "/" in new_name or "\\" in new_name:
        st.error("新名称不能包含路径分隔符")
        return False
    if Path(new_name).suffix:
        st.error("只能修改文件名，不能修改文件后缀")
        return False
    final_name = f"{new_name}{old_ext}"
    return handle_rename_path(str(old_path), final_name)

# 主程序逻辑

# 初始化状态
if "selected_path" not in st.session_state:
    st.session_state.selected_path = None
if "selected_type" not in st.session_state:
    st.session_state.selected_type = None

# 侧边栏构建
with st.sidebar:
    st.title("📂 目录管理")
    # 【修改点】 use_container_width=True -> width='stretch'
    if st.button("🔄 刷新磁盘列表", width='stretch'):
        st.cache_data.clear()
        st.rerun()
    
    st.write("---")
    # 启动递归渲染
    dir_tree = get_directory_tree(TARGET_DIR)
    render_tree_ui(dir_tree, Path(TARGET_DIR))

# 主界面显示预览
st.title("🖼️ 内容预览")

active_path = st.session_state.selected_path
active_type = st.session_state.selected_type
if active_path and os.path.exists(active_path):
    f_path = Path(active_path)
    
    # 顶部工具栏
    col_path, col_actions = st.columns([4, 2])
    with col_path:
        st.text(f"📍 路径: {f_path.relative_to(Path(TARGET_DIR).parent)}")
    with col_actions:
        if active_type == "file":
            # 【修改点】 Popover 也使用 width='stretch' (如果支持的话，若报错可改回 use_container_width 或移除)
            # 注意：st.popover 在某些版本可能没有 width 参数，如果报错请将下面这行改回 use_container_width=True
            with st.popover("🗑️ 删除文件", width='stretch'):
                st.error("确定要删除吗？")
                # 【修改点】 use_container_width=True -> width='stretch'
                if st.button("确认删除", type="primary", width='stretch'):
                    if handle_delete_file(active_path):
                        st.rerun()
            with st.popover("✏️ 重命名文件", width='stretch'):
                base_name = f_path.stem
                new_name = st.text_input("新名称（不含后缀）", value=base_name, key=f"rename_file_{active_path}")
                # 【修改点】 use_container_width=True -> width='stretch'
                if st.button("确认重命名", type="primary", width='stretch'):
                    if handle_rename_file(active_path, new_name):
                        st.rerun()
        elif active_type == "folder":
            with st.popover("🗑️ 删除文件夹", width='stretch'):
                st.error(f"是否删除{f_path.name}文件夹")
                # 【修改点】 use_container_width=True -> width='stretch'
                if st.button("确认删除", type="primary", width='stretch'):
                    if handle_delete_folder(active_path):
                        st.rerun()
            with st.popover("✏️ 重命名文件夹", width='stretch'):
                new_name = st.text_input("新名称", value=f_path.name, key=f"rename_folder_{active_path}")
                # 【修改点】 use_container_width=True -> width='stretch'
                if st.button("确认重命名", type="primary", width='stretch'):
                    if handle_rename_path(active_path, new_name):
                        st.rerun()

    st.divider()

    if active_type == "file":
        mtime = os.path.getmtime(f_path)
        # 根据后缀名预览
        try:
            if f_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
                # 【修改点】 use_container_width=True -> width='stretch'
                st.image(load_image_cached(f_path, mtime), width='stretch')
            elif f_path.suffix.lower() == ".jsonl":
                df = load_jsonl_cached(f_path, mtime)
                # 【修改点】 use_container_width=True -> width='stretch'
                st.dataframe(df, width='stretch', height=700)
            elif f_path.suffix.lower() == ".json":
                df = load_json_cached(f_path, mtime)
                # 【修改点】 use_container_width=True -> width='stretch'
                st.dataframe(df, width='stretch', height=700)
            else:
                st.info("该文件类型不支持预览。")
        except Exception as e:
            st.error(f"文件加载出错: {e}")
    else:
        st.info("已选择文件夹，可进行删除或重命名。")
else:
    st.info("👈 请从左侧文件夹中选择一个文件进行查看。")