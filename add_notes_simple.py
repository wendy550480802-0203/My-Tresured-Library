#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版：将四层笔记添加到HTML文件
直接精确匹配，不做模糊匹配
"""

import json
import re
from pathlib import Path

HTML_DIR = "/Users/liwenqi/My-Library-Notes"
NOTES_DIR = "/Users/liwenqi/Desktop/我的藏书阁/所有四层笔记"

def build_notes_dict():
    """构建 {基础文件名: 内容} 字典"""
    notes_dict = {}
    notes_path = Path(NOTES_DIR)
    
    if not notes_path.exists():
        print(f"错误：目录不存在 {NOTES_DIR}")
        return notes_dict
    
    for md_file in notes_path.glob("*"):
        if not md_file.is_file() or "四层笔记" not in md_file.name:
            continue
        
        # 提取基础文件名
        name = md_file.stem  # 移除 .md
        if " - 四层笔记" in name:
            base = name.replace(" - 四层笔记", "")
        elif "_四层笔记" in name:
            base = name.replace("_四层笔记", "")
        else:
            continue
        
        # 读取内容
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            notes_dict[base] = content
            notes_dict[base + ".md"] = content  # 也存储 .md 版本
        except Exception as e:
            print(f"✗ 读取失败: {md_file.name} - {e}")
    
    print(f"✓ 加载了 {len(notes_dict)} 个匹配项（来自 {len(list(notes_path.glob('*四层笔记*')))} 个文件）\n")
    return notes_dict

def process_html_file(html_file, notes_dict):
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
            
            node_id = node.get('id', '')
            title = node.get('title', '')
            label = node.get('label', '')
            
            notes_content = None
            for key in [node_id, title, label]:
                if key and key in notes_dict:
                    notes_content = notes_dict[key]
                    break
                # 尝试不带 .md 后缀
                if key and key.replace('.md', '') in notes_dict:
                    notes_content = notes_dict[key.replace('.md', '')]
                    break
            
            if notes_content:
                node['fourLayerNotes'] = notes_content
                updated += 1
        
        if updated == 0:
            print(f"  ○ 无匹配: {html_file.name} (节点数: {len(nodes)})")
            return 0
        
        # 写回文件
        new_nodes_str = json.dumps(nodes, ensure_ascii=False, indent=2)
        new_content = content.replace(nodes_str, new_nodes_str)
        
        # 添加显示四层笔记的代码（如果还没有）
        if 'fourLayerNotes' not in content[:content.find('fourLayerNotes') - 1 if 'fourLayerNotes' in content else 0]:
            # 在 showDetail 函数中添加显示代码
            marker = '/* 打开原文件'
            if marker in new_content and '四层笔记' not in new_content[:new_content.find(marker)]:
                new_code = '''  /* 四层笔记 */
  if(d.fourLayerNotes){
    html += '<div class="section"><div class="section-title">📚 四层笔记</div><div class="four-layer-notes">' + d.fourLayerNotes.replace(/# /g, '<h3>').replace(/## /g, '<h4>').replace(/\n\n/g, '<br><br>') + '</div></div>';
  }
  
  /* 打开原文件'''
                new_content = new_content.replace(marker, new_code)
        
        # 添加CSS（如果还没有）
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
    print("添加四层笔记到HTML文件（简化版）")
    print("=" * 60 + "\n")
    
    # 1. 加载四层笔记
    print("步骤1: 加载四层笔记...")
    notes_dict = build_notes_dict()
    
    if not notes_dict:
        print("错误：没有加载到任何四层笔记！")
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
        updated = process_html_file(html_file, notes_dict)
        total_updated += updated
    
    print("\n" + "=" * 60)
    print(f"完成！总共更新了 {total_updated} 个节点的四层笔记")
    print("=" * 60)

if __name__ == "__main__":
    main()
