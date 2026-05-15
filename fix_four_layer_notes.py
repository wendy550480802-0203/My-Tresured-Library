#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复四层笔记匹配脚本
- 正确匹配：文件名包含节点标题
- 修复JavaScript渲染逻辑
"""

import json
import re
from pathlib import Path

HTML_DIR = "/Users/liwenqi/My-Library-Notes"
NOTES_DIR = "/Users/liwenqi/Desktop/我的藏书阁/所有四层笔记"

def build_notes_index():
    """构建四层笔记索引：{清理后的书名: 内容}"""
    notes_index = {}
    notes_path = Path(NOTES_DIR)
    
    if not notes_path.exists():
        print(f"错误：目录不存在 {NOTES_DIR}")
        return notes_index
    
    for md_file in notes_path.glob("*"):
        if not md_file.is_file() or "四层笔记" not in md_file.name:
            continue
        
        # 提取书名
        name = md_file.stem  # 移除 .md
        
        # 移除可能的数字前缀
        base = re.sub(r'^\d+[\.\-\s]*', '', name)
        
        # 移除 " - 四层笔记" 或 "_四层笔记"
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

def clean_title(title):
    """清理标题：移除特殊字符，便于匹配"""
    if not title:
        return ""
    # 移除路径前缀
    title = title.replace("📖 ", "").replace("💡 ", "")
    # 移除.md后缀
    title = re.sub(r'\.md$', '', title)
    return title.strip()

def find_matching_notes(title, notes_index):
    """查找匹配的四层笔记 - 匹配规则：文件名包含节点标题"""
    if not title:
        return None
    
    title_clean = clean_title(title)
    
    # 1. 精确匹配
    if title_clean in notes_index:
        return notes_index[title_clean]
    
    # 2. 模糊匹配：文件名包含标题 或 标题包含文件名
    for book_title, content in notes_index.items():
        if title_clean in book_title or book_title in title_clean:
            return content
    
    # 3. 清理后匹配（移除标点符号）
    title_no_punct = re.sub(r'[^\w\s]', '', title_clean)
    for book_title, content in notes_index.items():
        book_no_punct = re.sub(r'[^\w\s]', '', book_title)
        if title_no_punct in book_no_punct or book_no_punct in title_no_punct:
            return content
    
    return None

def add_js_rendering(html_content):
    """添加/修复JavaScript渲染四层笔记的代码"""
    
    # 检查是否已经有四层笔记的渲染代码
    if 'fourLayerNotes' in html_content and 'showDetail' in html_content:
        # 修复已有的渲染代码
        # 找到showDetail函数，替换四层笔记的渲染部分
        
        # 新的渲染代码（使用marked.js或手动转换markdown）
        new_rendering = r'''  /* 四层笔记 */
  if(d.fourLayerNotes){
    var notesHtml = d.fourLayerNotes;
    // Markdown转HTML（简单版）
    notesHtml = notesHtml.replace(/^# (.*)$/gm, '<h3>$1</h3>');
    notesHtml = notesHtml.replace(/^## (.*)$/gm, '<h4>$1</h4>');
    notesHtml = notesHtml.replace(/^### (.*)$/gm, '<h5>$1</h5>');
    notesHtml = notesHtml.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    notesHtml = notesHtml.replace(/^- (.*)$/gm, '<li>$1</li>');
    notesHtml = notesHtml.replace(/\n\n/g, '<br><br>');
    notesHtml = notesHtml.replace(/\n/g, '<br>');
    html += '<div class="section"><div class="section-title">📚 四层笔记</div><div class="four-layer-notes">' + notesHtml + '</div></div>';
  }'''
        
        # 使用正则表达式替换旧的渲染代码
        # 注意：re.sub的replacement如果是字符串，会处理反斜杠转义
        # 所以使用lambda函数来避免这个问题
        pattern = r'/\* 四层笔记 \*/[\s\S]*?/\* 打开原文件'
        replacement_text = new_rendering + '\n\n  /* 打开原文件'
        
        new_content = re.sub(pattern, lambda m: replacement_text, html_content)
        
        if new_content == html_content:
            # 没找到标记，尝试直接添加到showDetail函数
            insert_point = html_content.find('/* 打开原文件')
            if insert_point > 0:
                new_content = html_content[:insert_point] + new_rendering + '\n\n' + html_content[insert_point:]
        
        return new_content
    
    return html_content

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
        
        # 添加/修复四层笔记（强制重新匹配）
        updated = 0
        for node in nodes:
            title = node.get('title', '')
            if not title:
                continue
            
            # 强制重新匹配（覆盖已有的错误匹配）
            notes_content = find_matching_notes(title, notes_index)
            if notes_content:
                node['fourLayerNotes'] = notes_content
                updated += 1
            elif 'fourLayerNotes' in node:
                # 移除错误的匹配
                del node['fourLayerNotes']
        
        if updated == 0:
            print(f"  ○ 无匹配: {html_file.name} (节点数: {len(nodes)})")
            return 0
        
        # 写回文件
        new_nodes_str = json.dumps(nodes, ensure_ascii=False, indent=2)
        new_content = content.replace(nodes_str, new_nodes_str)
        
        # 添加/修复JavaScript渲染代码
        new_content = add_js_rendering(new_content)
        
        # 添加CSS（如果还没有）
        if 'four-layer-notes' not in new_content:
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
            new_content = new_content.replace('</head>', css + '</head>')
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✓ 更新了 {updated}/{len(nodes)} 个节点: {html_file.name}")
        return updated
        
    except Exception as e:
        print(f"  ✗ 处理失败 {html_file.name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    print("=" * 60)
    print("修复四层笔记匹配")
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
