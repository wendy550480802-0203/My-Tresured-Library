#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复四层笔记匹配脚本 v4 - 极简版
- 对于书籍节点，直接在四层笔记目录中查找文件名包含节点标题的文件
- 找到就匹配，找不到就不匹配
"""

import json
import re
from pathlib import Path

HTML_DIR = "/Users/liwenqi/My-Library-Notes"
NOTES_DIR = "/Users/liwenqi/Desktop/我的藏书阁/所有四层笔记"

def find_matching_notes(title):
    """直截了当的匹配：在目录中查找文件名包含标题的文件"""
    if not title:
        return None
    
    # 清理标题
    title_clean = title.replace("📖 ", "").replace("💡 ", "").strip()
    title_clean = re.sub(r'\.md$', '', title_clean)
    
    # 在目录中查找文件
    notes_path = Path(NOTES_DIR)
    for md_file in notes_path.glob("*"):
        if not md_file.is_file() or "四层笔记" not in md_file.name:
            continue
        
        # 检查文件名是否包含节点标题
        if title_clean in md_file.name:
            try:
                return md_file.read_text('utf-8')
            except:
                return None
    
    # 没找到
    return None

def process_html_file(html_file):
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
        
        # 重新匹配所有书籍节点的四层笔记
        updated = 0
        for node in nodes:
            # 只给书籍节点添加四层笔记
            if node.get('type') != 'book':
                if 'fourLayerNotes' in node:
                    del node['fourLayerNotes']
                continue
            
            title = node.get('title', '')
            if not title:
                if 'fourLayerNotes' in node:
                    del node['fourLayerNotes']
                continue
            
            # 查找匹配的四层笔记
            notes_content = find_matching_notes(title)
            if notes_content:
                node['fourLayerNotes'] = notes_content
                updated += 1
            elif 'fourLayerNotes' in node:
                # 移除错误的匹配
                del node['fourLayerNotes']
        
        if updated == 0:
            book_count = sum(1 for n in nodes if n.get('type') == 'book')
            print(f"  ○ 无匹配: {html_file.name} (书籍节点: {book_count})")
            return 0
        
        # 写回文件
        new_nodes_str = json.dumps(nodes, ensure_ascii=False, indent=2)
        new_content = content.replace(nodes_str, new_nodes_str)
        
        # 确保JavaScript渲染代码正确
        new_content = ensure_js_rendering(new_content)
        
        # 确保CSS存在
        new_content = ensure_css(new_content)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        book_count = sum(1 for n in nodes if n.get('type') == 'book')
        print(f"  ✓ 更新了 {updated}/{book_count} 个书籍节点: {html_file.name}")
        return updated
        
    except Exception as e:
        print(f"  ✗ 处理失败 {html_file.name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def ensure_js_rendering(html_content):
    """确保JavaScript渲染代码正确"""
    # 正确的渲染代码
    correct_js = '''  /* 四层笔记 */
  if(d.fourLayerNotes){
    var notesHtml = d.fourLayerNotes;
    // 简单的markdown转HTML
    notesHtml = notesHtml.replace(/^# (.*)$/gm, '<h3>$1</h3>');
    notesHtml = notesHtml.replace(/^## (.*)$/gm, '<h4>$1</h4>');
    notesHtml = notesHtml.replace(/^### (.*)$/gm, '<h5>$1</h5>');
    notesHtml = notesHtml.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    notesHtml = notesHtml.replace(/^- (.*)$/gm, '<li>$1</li>');
    notesHtml = notesHtml.replace(/\n\n/g, '<br><br>');
    notesHtml = notesHtml.replace(/\n/g, '<br>');
    html += '<div class="section"><div class="section-title">📚 四层笔记</div><div class="four-layer-notes">' + notesHtml + '</div></div>';
  }'''
    
    # 检查是否已有四层笔记的渲染代码
    if 'fourLayerNotes' in html_content and 'showDetail' in html_content:
        # 查找并替换旧的渲染代码
        pattern = r'/\* 四层笔记 \*/[\s\S]*?/\* 打开原文件'
        replacement = correct_js + '\n\n  /* 打开原文件'
        
        new_content = re.sub(pattern, replacement, html_content)
        
        if new_content != html_content:
            return new_content
        
        # 如果没找到，尝试直接插入
        insert_point = html_content.find('/* 打开原文件')
        if insert_point > 0:
            return html_content[:insert_point] + correct_js + '\n\n' + html_content[insert_point:]
    
    return html_content

def ensure_css(html_content):
    """确保CSS样式存在"""
    if 'four-layer-notes' in html_content:
        return html_content
    
    css = '''
  <style>
    .four-layer-notes {
      font-size: 13px;
      line-height: 1.8;
      color: #cbd5e1;
      max-height: 600px;
      overflow-y: auto;
      padding: 16px;
      background: #0f172a;
      border-radius: 8px;
      margin-top: 12px;
      border: 1px solid #334155;
    }
    .four-layer-notes h3 {
      color: #67e8f9;
      font-size: 15px;
      margin: 20px 0 12px 0;
      border-bottom: 1px solid #334155;
      padding-bottom: 8px;
    }
    .four-layer-notes h4 {
      color: #94a3b8;
      font-size: 14px;
      margin: 16px 0 8px 0;
    }
    .four-layer-notes h5 {
      color: #a5b4fc;
      font-size: 13px;
      margin: 12px 0 6px 0;
    }
    .four-layer-notes strong {
      color: #f1f5f9;
    }
    .four-layer-notes li {
      margin-left: 20px;
    }
  </style>
'''
    return html_content.replace('</head>', css + '</head>')

def main():
    print("=" * 60)
    print("修复四层笔记匹配 v4 - 极简版")
    print("=" * 60 + "\n")
    
    # 处理HTML文件
    html_dir = Path(HTML_DIR)
    html_files = [f for f in html_dir.glob("*.html") 
                  if f.name not in ['index.html', 'knowledge_graph_v6.html', 'template_with_markers.html']]
    
    print(f"找到 {len(html_files)} 个HTML文件\n")
    
    total_updated = 0
    for i, html_file in enumerate(html_files, 1):
        print(f"[{i}/{len(html_files)}] {html_file.name}")
        updated = process_html_file(html_file)
        total_updated += updated
    
    print("\n" + "=" * 60)
    print(f"完成！总共更新了 {total_updated} 个节点的四层笔记")
    print("=" * 60)

if __name__ == "__main__":
    main()
