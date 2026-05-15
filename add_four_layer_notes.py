#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将四层笔记内容添加到知识图谱HTML文件中
"""

import os
import json
import re
from pathlib import Path

# 配置路径
HTML_DIR = "/Users/liwenqi/My-Library-Notes"
NOTES_DIR = "/Users/liwenqi/Desktop/我的藏书阁/所有四层笔记"

def load_four_layer_notes():
    """加载所有四层笔记文件，返回 {文件名: 内容} 的字典"""
    notes_dict = {}
    
    notes_path = Path(NOTES_DIR)
    if not notes_path.exists():
        print(f"错误：四层笔记目录不存在: {NOTES_DIR}")
        return notes_dict
    
    for md_file in notes_path.glob("* - 四层笔记.md"):
        # 从文件名提取原始文件名
        # 例如："服务组合 - 四层笔记.md" -> "服务组合.md"
        original_name = md_file.stem.replace(" - 四层笔记", "") + ".md"
        
        # 读取文件内容
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                notes_dict[original_name] = content
                print(f"✓ 加载四层笔记: {original_name}")
        except Exception as e:
            print(f"✗ 读取失败 {md_file.name}: {e}")
    
    print(f"\n总共加载了 {len(notes_dict)} 个四层笔记文件\n")
    return notes_dict

def extract_nodes_from_html(html_content):
    """从HTML内容中提取NODES数组"""
    # 查找 var NODES = [...] 模式
    match = re.search(r'var NODES = (\[.*?\]);', html_content, re.DOTALL)
    if not match:
        return None, None
    
    nodes_str = match.group(1)
    try:
        # 将JavaScript数组转换为有效的JSON
        # 处理JavaScript中的单引号、尾逗号等
        nodes_json = nodes_str
        # 移除尾逗号
        nodes_json = re.sub(r',\s*\]', ']', nodes_json)
        nodes_json = re.sub(r',\s*\}', '}', nodes_json)
        
        nodes = json.loads(nodes_json)
        return nodes, match.start(1)
    except Exception as e:
        print(f"解析NODES失败: {e}")
        return None, None

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
        
        # 提取并解析NODES
        nodes_str = nodes_match.group(1)
        # 尝试直接解析（假设是有效的JSON）
        try:
            nodes = json.loads(nodes_str)
        except:
            # 如果不是有效JSON，跳过
            print(f"  ✗ NODES不是有效JSON: {html_file.name}")
            return False
        
        # 为每个节点添加四层笔记
        updated_count = 0
        for node in nodes:
            node_id = node.get('id', '')
            if node_id in notes_dict:
                node['fourLayerNotes'] = notes_dict[node_id]
                updated_count += 1
        
        # 重新序列化为JSON
        new_nodes_str = json.dumps(nodes, ensure_ascii=False, indent=2)
        
        # 替换原NODES数组
        new_content = content.replace(nodes_str, new_nodes_str)
        
        # 修改showDetail函数以显示四层笔记
        # 查找并替换showDetail函数中的HTML生成部分
        old_detail_html = '''  /* 打开原文件：用 Obsidian URI 协议，避免浏览器 file:// 限制 */
  if(d.path){
    var obsidianUrl = "obsidian://open?path=" + encodeURIComponent(d.path);
    html += '<div class="section"><a class="open-link" href="' + obsidianUrl + '">📂 在 Obsidian 中打开</a></div>';
  }'''
        
        new_detail_html = r'''  /* 四层笔记 */
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
  }
  
  /* 打开原文件：用 Obsidian URI 协议，避免浏览器 file:// 限制 */
  if(d.path){
    var obsidianUrl = "obsidian://open?path=" + encodeURIComponent(d.path);
    html += '<div class="section"><a class="open-link" href="' + obsidianUrl + '">📂 在 Obsidian 中打开</a></div>';
  }'''
        
        if old_detail_html in new_content:
            new_content = new_content.replace(old_detail_html, new_detail_html)
            print(f"  ✓ 更新了showDetail函数: {html_file.name}")
        
        # 添加四层笔记的CSS样式
        css_style = '''
  <style>
    .four-layer-notes {
      font-size: 12px;
      line-height: 1.6;
      color: #cbd5e1;
      max-height: 400px;
      overflow-y: auto;
      padding: 10px;
      background: #0f172a;
      border-radius: 6px;
      margin-top: 8px;
    }
    .four-layer-notes h3 {
      color: #67e8f9;
      font-size: 14px;
      margin: 12px 0 8px 0;
      border-bottom: 1px solid #334155;
      padding-bottom: 4px;
    }
    .four-layer-notes h4 {
      color: #94a3b8;
      font-size: 13px;
      margin: 10px 0 6px 0;
    }
  </style>'''
        
        if '<style>' in new_content and 'four-layer-notes' not in new_content:
            new_content = new_content.replace('</style>', '</style>' + css_style)
        
        # 写回文件
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✓ 更新了 {updated_count}/{len(nodes)} 个节点的四层笔记: {html_file.name}")
        return True
        
    except Exception as e:
        print(f"  ✗ 处理失败 {html_file.name}: {e}")
        return False

def main():
    print("=" * 60)
    print("开始添加四层笔记到知识图谱HTML文件")
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
