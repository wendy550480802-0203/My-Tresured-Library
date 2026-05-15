#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四层笔记匹配脚本（文件名包含节点标题）
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher

HTML_DIR = "/Users/liwenqi/My-Library-Notes"
NOTES_DIR = "/Users/liwenqi/Desktop/我的藏书阁/所有四层笔记"

def build_notes_index():
    """构建四层笔记索引：{文件名中的书名: 内容}"""
    notes_index = {}
    notes_path = Path(NOTES_DIR)
    
    if not notes_path.exists():
        print(f"错误：目录不存在 {NOTES_DIR}")
        return notes_index
    
    for md_file in notes_path.glob("*"):
        if not md_file.is_file() or "四层笔记" not in md_file.name:
            continue
        
        # 提取书名（移除" - 四层笔记.md" 或 "_四层笔记.md"）
        name = md_file.stem  # 移除 .md
        
        # 移除可能的数字前缀（如 "0107"、"01 - " 等）
        base = re.sub(r'^\d+[\.\-\s]*', '', name)  # 移除开头的数字和符号
        
        if " - 四层笔记" in base:
            book_title = base.replace(" - 四层笔记", "")
        elif "_四层笔记" in base:
            book_title = base.replace("_四层笔记", "")
        else:
            continue
        
        # 读取内容
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            notes_index[book_title.strip()] = content
        except Exception as e:
            print(f"✗ 读取失败: {md_file.name} - {e}")
    
    print(f"✓ 构建了 {len(notes_index)} 个四层笔记索引项\n")
    return notes_index

def find_matching_notes(title, notes_index):
    """查找匹配的四层笔记（精确匹配 + 模糊匹配）"""
    if not title:
        return None
    
    # 1. 精确匹配
    if title in notes_index:
        return notes_index[title]
    
    # 2. 模糊匹配（标题是文件名的子集）
    for book_title, content in notes_index.items():
        if title in book_title or book_title in title:
            return content
    
    # 3. 相似度匹配（相似度 > 0.85）
    best_match = None
    best_ratio = 0.85
    
    for book_title, content in notes_index.items():
        ratio = SequenceMatcher(None, title, book_title).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = content
    
    return best_match

def process_html_file(html_file, notes_index):
    """处理单个HTML文件"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取NODES
        match = re.search(r'var NODES = (\[.*?\]);', content, re.DOTALL)
        if not match:
            return 0
        
        nodes_str = match.group(1)
        
        # 解析JSON（处理尾逗号）
        nodes_str_clean = re.sub(r',\s*\]', ']', nodes_str)
        nodes_str_clean = re.sub(r',\s*\}', '}', nodes_str_clean)
        
        try:
            nodes = json.loads(nodes_str_clean)
        except:
            print(f"  ✗ JSON解析失败: {html_file.name}")
            return 0
        
        # 添加四层笔记
        updated = 0
        for node in nodes:
            if 'fourLayerNotes' in node:
                continue
            
            title = node.get('title', '')
            if not title:
                continue
            
            notes_content = find_matching_notes(title, notes_index)
            if notes_content:
                node['fourLayerNotes'] = notes_content
                updated += 1
        
        if updated == 0:
            print(f"  ○ 无匹配: {html_file.name} (节点数: {len(nodes)})")
            return 0
        
        # 写回文件
        new_nodes_str = json.dumps(nodes, ensure_ascii=False, indent=2)
        new_content = content.replace(nodes_str, new_nodes_str)
        
        # 添加显示四层笔记的代码
        marker = '/* 打开原文件'
        if marker in new_content and '四层笔记' not in new_content[:new_content.find(marker)]:
            new_code = '''  /* 四层笔记 */
  if(d.fourLayerNotes){
    var notesHtml = d.fourLayerNotes
      .replace(/# 第一层[\s\S]*?第二层/g, '<h3>第一层：核心论点</h3>')
      .replace(/# 第二层[\s\S]*?第三层/g, '<h3>第二层：论证与细节</h3>')
      .replace(/# 第三层[\s\S]*?第四层/g, '<h3>第三层：思想关联与延伸</h3>')
      .replace(/# 第四层[\s\S]*?$/g, '<h3>第四层：批判性思考</h3>')
      .replace(/## /g, '<h4>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
    html += '<div class="section"><div class="section-title">📚 四层笔记</div><div class="four-layer-notes">' + notesHtml + '</div></div>';
  }
  
  /* 打开原文件'''
            new_content = new_content.replace(marker, new_code)
        
        # 添加CSS
        if 'four-layer-notes' not in new_content:
            css = '''
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
            new_content = new_content.replace('</head>', css + '</head>')
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✓ 更新了 {updated}/{len(nodes)} 个节点: {html_file.name}")
        return updated
        
    except Exception as e:
        print(f"  ✗ 处理失败 {html_file.name}: {e}")
        return 0

def main():
    print("=" * 60)
    print("添加四层笔记到HTML文件（文件名包含标题匹配）")
    print("=" * 60 + "\n")
    
    # 1. 构建四层笔记索引
    print("步骤1: 构建四层笔记索引...")
    notes_index = build_notes_index()
    
    if not notes_index:
        print("错误：没有成功构建索引！")
        return
    
    # 2. 处理HTML文件
    print("步骤2: 处理HTML文件...\n")
    html_dir = Path(HTML_DIR)
    html_files = [f for f in html_dir.glob("*.html") 
                  if f.name not in ['index.html', 'knowledge_graph_v6.html', 'template_with_markers.html']]
    
    print(f"找到 {len(html_files)} 个HTML文件\n")
    
    total_updated = 0
    for i, html_file in enumerate(html_files, 1):
        print(f"[{i}/{len(html_files)}] {html_file.name}")
        updated = process_html_file(html_file, notes_index)
        total_updated += updated
    
    print("\n" + "=" * 60)
    print(f"完成！总共更新了 {total_updated} 个节点的四层笔记")
    print("=" * 60)

if __name__ == "__main__":
    main()
