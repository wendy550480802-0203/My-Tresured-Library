#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将四层笔记内容添加到知识图谱HTML文件中（修复版）
处理两种文件名格式：XXX_四层笔记.md 和 XXX - 四层笔记.md
"""

import os
import json
import re
from pathlib import Path
from difflib import SequenceMatcher

# 配置路径
HTML_DIR = "/Users/liwenqi/My-Library-Notes"
NOTES_DIR = "/Users/liwenqi/Desktop/我的藏书阁/所有四层笔记"

def normalize_filename(name):
    """标准化文件名，用于匹配"""
    # 移除.md后缀
    name = name.replace('.md', '')
    # 移除常见的前缀数字和符号
    name = re.sub(r'^\d+[\.\-\s]*', '', name)
    # 移除特殊符号
    name = re.sub(r'[【】()（）]', '', name)
    return name.strip()

def load_four_layer_notes():
    """加载所有四层笔记文件，返回 {可能的节点ID: 内容} 的字典"""
    notes_dict = {}
    
    notes_path = Path(NOTES_DIR)
    if not notes_path.exists():
        print(f"错误：四层笔记目录不存在: {NOTES_DIR}")
        return notes_dict
    
    for md_file in notes_path.glob("*.md"):
        if "四层笔记" not in md_file.name:
            continue
            
        # 提取基础文件名（移除"四层笔记"后缀）
        name = md_file.stem  # 移除.md
        if name.endswith("四层笔记"):
            base_name = name.replace(" - 四层笔记", "").replace("_四层笔记", "")
        else:
            continue
        
        # 生成可能的节点ID（多种格式）
        possible_ids = [
            base_name + ".md",  # 标准格式
            base_name + ".MD",  # 大写后缀
        ]
        
        # 读取文件内容
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pid in possible_ids:
                notes_dict[pid] = content
            
            # 同时存储标准化后的名称（用于模糊匹配）
            normalized = normalize_filename(base_name)
            notes_dict[normalized] = content
            
            print(f"✓ 加载四层笔记: {base_name}")
        except Exception as e:
            print(f"✗ 读取失败 {md_file.name}: {e}")
    
    print(f"\n总共加载了 {len(notes_dict)} 个四层笔记匹配项\n")
    return notes_dict

def find_matching_notes(node, notes_dict):
    """为节点查找匹配的四层笔记"""
    # 尝试精确匹配 id
    node_id = node.get('id', '')
    if node_id in notes_dict:
        return notes_dict[node_id]
    
    # 尝试精确匹配 title
    title = node.get('title', '')
    if title + ".md" in notes_dict:
        return notes_dict[title + ".md"]
    
    # 尝试精确匹配 label
    label = node.get('label', '')
    if label + ".md" in notes_dict:
        return notes_dict[label + ".md"]
    
    # 尝试标准化匹配
    for key in ['id', 'title', 'label']:
        value = node.get(key, '')
        if value:
            normalized = normalize_filename(value)
            if normalized in notes_dict:
                return notes_dict[normalized]
    
    # 模糊匹配（相似度>0.8）
    for key in ['id', 'title', 'label']:
        value = node.get(key, '')
        if not value:
            continue
        value_base = value.replace('.md', '')
        for note_key in notes_dict:
            if isinstance(note_key, str) and len(note_key) > 5:
                ratio = SequenceMatcher(None, value_base, note_key.replace('.md', '')).ratio()
                if ratio > 0.85:
                    return notes_dict[note_key]
    
    return None

def update_html_file(html_file, notes_dict):
    """更新单个HTML文件，添加四层笔记内容"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取NODES数组
        nodes_match = re.search(r'var NODES = (\[.*?\]);', content, re.DOTALL)
        if not nodes_match:
            print(f"  ✗ 未找到NODES数组: {html_file.name}")
            return False
        
        nodes_str = nodes_match.group(1)
        
        # 预处理JSON字符串
        nodes_str_clean = nodes_str
        # 移除JavaScript中的尾逗号
        nodes_str_clean = re.sub(r',\s*\]', ']', nodes_str_clean)
        nodes_str_clean = re.sub(r',\s*\}', '}', nodes_str_clean)
        
        try:
            nodes = json.loads(nodes_str_clean)
        except:
            print(f"  ✗ NODES不是有效JSON: {html_file.name}")
            return False
        
        # 为每个节点添加四层笔记
        updated_count = 0
        for node in nodes:
            if 'fourLayerNotes' not in node:
                notes_content = find_matching_notes(node, notes_dict)
                if notes_content:
                    node['fourLayerNotes'] = notes_content
                    updated_count += 1
        
        # 重新序列化为JSON
        new_nodes_str = json.dumps(nodes, ensure_ascii=False, indent=2)
        
        # 替换原NODES数组
        new_content = content.replace(nodes_str, new_nodes_str)
        
        # 修改showDetail函数以显示四层笔记
        # 查找详情面板的HTML生成部分
        old_marker = '/* 打开原文件'
        new_code = '''  /* 四层笔记 */
  if(d.fourLayerNotes){
    var notesHtml = d.fourLayerNotes
      .replace(/# 第一层/g, '<h3>第一层：核心论点</h3>')
      .replace(/# 第二层/g, '<h3>第二层：论证与细节</h3>')
      .replace(/# 第三层/g, '<h3>第三层：思想关联与延伸</h3>')
      .replace(/# 第四层/g, '<h3>第四层：批判性思考</h3>')
      .replace(/##/g, '<h4>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
    html += '<div class="section"><div class="section-title">📚 四层笔记</div><div class="four-layer-notes">' + notesHtml + '</div></div>';
  }
  
  /* 打开原文件'''
        
        if old_marker in new_content and 'fourLayerNotes' not in new_content[:new_content.find(old_marker)]:
            new_content = new_content.replace(old_marker, new_code)
            print(f"  ✓ 更新了showDetail函数: {html_file.name}")
        
        # 添加CSS样式（如果还没有）
        if 'four-layer-notes' not in new_content:
            css_style = '''
  <style>
    .four-layer-notes {
      font-size: 12px;
      line-height: 1.6;
      color: #cbd5e1;
      max-height: 500px;
      overflow-y: auto;
      padding: 12px;
      background: #0f172a;
      border-radius: 6px;
      margin-top: 10px;
      border: 1px solid #334155;
    }
    .four-layer-notes h3 {
      color: #67e8f9;
      font-size: 14px;
      margin: 16px 0 10px 0;
      border-bottom: 1px solid #334155;
      padding-bottom: 6px;
    }
    .four-layer-notes h4 {
      color: #94a3b8;
      font-size: 13px;
      margin: 12px 0 6px 0;
    }
  </style>
'''
            # 在</head>前插入样式
            new_content = new_content.replace('</head>', css_style + '</head>')
        
        # 写回文件
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✓ 更新了 {updated_count}/{len(nodes)} 个节点的四层笔记: {html_file.name}")
        return True
        
    except Exception as e:
        print(f"  ✗ 处理失败 {html_file.name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("开始添加四层笔记到知识图谱HTML文件（修复版）")
    print("=" * 60 + "\n")
    
    # 1. 加载所有四层笔记
    print("步骤1：加载四层笔记文件...")
    notes_dict = load_four_layer_notes()
    
    if not notes_dict:
        print("错误：没有成功加载任何四层笔记文件！")
        return
    
    # 2. 处理所有HTML文件
    print("步骤2：处理HTML文件...\n")
    html_dir = Path(HTML_DIR)
    
    html_files = list(html_dir.glob("*.html"))
    html_files = [f for f in html_files if f.name != 'index.html' and f.name != 'knowledge_graph_v6.html']
    
    print(f"找到 {len(html_files)} 个HTML文件需要处理\n")
    
    success_count = 0
    for i, html_file in enumerate(html_files, 1):
        print(f"[{i}/{len(html_files)}] 处理: {html_file.name}")
        if update_html_file(html_file, notes_dict):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"完成！成功更新了 {success_count}/{len(html_files)} 个HTML文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
