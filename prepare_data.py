import json
from pathlib import Path

def prepare_visualization_data(input_file="alice_chunks_with_kg.json", output_dir="data"):
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 读取原始数据
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 {input_file}")
        print("请确保alice_chunks_with_kg.json文件在当前目录")
        return
    except json.JSONDecodeError as e:
        print(f"❌ 错误：JSON文件格式有误: {e}")
        return
    
    print("🔍 分析数据结构...")
    
    # 获取元数据
    metadata = data.get('metadata', {})
    
    # 获取chunks的汇总和详细信息
    chunks_summary = data.get('chunks_summary', [])
    chunks_detail = data.get('chunks_detail', [])
    
    # 创建一个映射，方便查找
    summary_map = {chunk['chunk_id']: chunk for chunk in chunks_summary}
    
    # 处理每个chunk
    chunks_data = []
    total_entities = 0
    total_relationships = 0
    total_events = 0
    
    for i, chunk_detail in enumerate(chunks_detail):
        chunk_id = chunk_detail.get('chunk_id', i)
        
        # 获取对应的summary信息
        chunk_summary = summary_map.get(chunk_id, {})
        
        # 提取基本信息
        chunk_text = chunk_detail.get('chunk_text', '')
        chunk_metadata = chunk_detail.get('chunk_metadata', {})
        text_length = chunk_metadata.get('text_length', len(chunk_text))
        
        # 获取知识图谱
        knowledge_graph = chunk_detail.get('knowledge_graph', {})
        
        # 提取各种实体和关系
        entities = knowledge_graph.get('entities', [])
        relationships = knowledge_graph.get('relationships', [])
        key_events = knowledge_graph.get('key_events', [])
        
        # 从实体中分类出地点和角色
        locations = []
        characters = []
        objects = []
        
        for entity in entities:
            entity_type = entity.get('type', '').upper()
            if entity_type == 'LOCATION':
                locations.append(entity)
            elif entity_type in ['PERSON', 'CHARACTER', 'CREATURE']:
                characters.append(entity)
            elif entity_type == 'OBJECT':
                objects.append(entity)
        
        # 使用summary中的统计数据（如果有）或计算实际数量
        num_entities = chunk_summary.get('num_entities', len(entities))
        num_relationships = chunk_summary.get('num_relationships', len(relationships))
        num_events = chunk_summary.get('num_events', len(key_events))
        
        chunk_info = {
            'id': chunk_id,
            'text': chunk_text,
            'text_preview': chunk_text[:500] + '...' if len(chunk_text) > 500 else chunk_text,
            'text_length': text_length,
            'chapter': chunk_metadata.get('chapter', 'Unknown'),
            'kg': {
                'entities': entities,
                'relationships': relationships,
                'locations': locations,
                'characters': characters,
                'objects': objects,
                'key_events': key_events,
                'stats': {
                    'num_entities': num_entities,
                    'num_relationships': num_relationships,
                    'num_locations': len(locations),
                    'num_characters': len(characters),
                    'num_objects': len(objects),
                    'num_events': num_events
                }
            },
            'metadata': {
                'has_error': chunk_summary.get('has_error', False),
                'generation_time': chunk_summary.get('generation_time', 0),
                'chapter': chunk_metadata.get('chapter', 'Unknown'),
                'start_position': chunk_metadata.get('start_position', 0),
                'end_position': chunk_metadata.get('end_position', 0)
            }
        }
        
        chunks_data.append(chunk_info)
        
        # 更新总计
        total_entities += num_entities
        total_relationships += num_relationships
        total_events += num_events
        
        # 打印前几个chunk的详细信息
        if i < 3:
            print(f"\n📊 Chunk {chunk_id} 的统计信息:")
            print(f"   - 章节: {chunk_info['metadata']['chapter']}")
            print(f"   - 文本长度: {text_length}")
            print(f"   - 实体数量: {num_entities}")
            if entities:
                entity_types = set(e.get('type', 'UNKNOWN') for e in entities)
                print(f"     • 实体类型: {', '.join(entity_types)}")
                print(f"     • 地点: {len(locations)} 个")
                print(f"     • 角色: {len(characters)} 个")
                print(f"     • 物品: {len(objects)} 个")
            print(f"   - 关系数量: {num_relationships}")
            print(f"   - 事件数量: {num_events}")
            
            # 显示一些实体示例
            if entities and i == 0:
                print(f"\n   实体示例:")
                for j, entity in enumerate(entities[:3]):
                    print(f"     {j+1}. {entity.get('name', 'Unknown')} ({entity.get('type', 'Unknown')})")
                    if entity.get('description'):
                        desc = entity['description'][:100] + '...' if len(entity.get('description', '')) > 100 else entity['description']
                        print(f"        {desc}")
    
    # 创建汇总数据
    summary_data = {
        'metadata': {
            **metadata,
            'total_chunks': len(chunks_data),
            'total_entities': total_entities,
            'total_relationships': total_relationships,
            'total_events': total_events,
            'source_file': input_file
        },
        'chunks': chunks_data
    }
    
    # 保存完整数据
    all_chunks_file = output_path / "all_chunks.json"
    with open(all_chunks_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    # 保存简化的统计数据
    stats_file = output_path / "chunks_stats.json"
    stats_data = []
    for chunk in chunks_data:
        stats_data.append({
            'id': chunk['id'],
            'chapter': chunk.get('chapter', chunk['metadata'].get('chapter', 'Unknown')),
            'text_length': chunk['text_length'],
            'stats': chunk['kg']['stats']
        })
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=2, ensure_ascii=False)
    
    # 保存实体汇总
    entities_file = output_path / "entities_summary.json"
    all_entities = []
    all_locations = []
    all_characters = []
    
    for chunk in chunks_data:
        for entity in chunk['kg']['entities']:
            entity_with_chunk = {**entity, 'chunk_id': chunk['id']}
            all_entities.append(entity_with_chunk)
            
            if entity.get('type') == 'LOCATION':
                all_locations.append(entity_with_chunk)
            elif entity.get('type') in ['PERSON', 'CHARACTER', 'CREATURE']:
                all_characters.append(entity_with_chunk)
    
    entities_summary = {
        'total_entities': len(all_entities),
        'total_unique_locations': len(set(e['name'] for e in all_locations if 'name' in e)),
        'total_unique_characters': len(set(e['name'] for e in all_characters if 'name' in e)),
        'entities': all_entities[:100],  # 只保存前100个作为示例
        'main_locations': list({e['name']: e for e in all_locations if 'name' in e}.values())[:20],
        'main_characters': list({e['name']: e for e in all_characters if 'name' in e}.values())[:20]
    }
    
    with open(entities_file, 'w', encoding='utf-8') as f:
        json.dump(entities_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 数据准备完成！")
    print(f"   - 处理了 {len(chunks_data)} 个chunks")
    print(f"   - 总实体数: {total_entities}")
    print(f"   - 总关系数: {total_relationships}")
    print(f"   - 总事件数: {total_events}")
    print(f"   - 数据保存在 {output_dir}/ 目录:")
    print(f"     • 完整数据: all_chunks.json")
    print(f"     • 统计数据: chunks_stats.json")
    print(f"     • 实体汇总: entities_summary.json")

def inspect_data_structure(input_file="alice_chunks_with_kg.json"):
    """深入检查数据文件的实际结构"""
    print("🔍 检查数据文件结构...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 无法读取文件: {e}")
        return
    
    # 检查顶层结构
    if isinstance(data, dict):
        print(f"✓ 数据是一个字典，包含键: {list(data.keys())}")
        
        # 检查metadata
        if 'metadata' in data:
            print(f"\n📋 Metadata:")
            for key, value in data['metadata'].items():
                if not isinstance(value, (list, dict)):
                    print(f"   - {key}: {value}")
        
        # 检查chunks_summary
        if 'chunks_summary' in data and data['chunks_summary']:
            print(f"\n📊 Chunks Summary: {len(data['chunks_summary'])} 个chunks")
            print(f"   第一个chunk的字段: {list(data['chunks_summary'][0].keys())}")
        
        # 检查chunks_detail
        if 'chunks_detail' in data and data['chunks_detail']:
            print(f"\n📚 Chunks Detail: {len(data['chunks_detail'])} 个chunks")
            first_chunk = data['chunks_detail'][0]
            print(f"   第一个chunk的字段: {list(first_chunk.keys())}")
            
            # 检查knowledge_graph结构
            if 'knowledge_graph' in first_chunk:
                kg = first_chunk['knowledge_graph']
                print(f"\n   Knowledge Graph 字段:")
                for key in kg.keys():
                    if isinstance(kg[key], list):
                        print(f"     - {key}: 列表，包含 {len(kg[key])} 个元素")
                        if kg[key] and isinstance(kg[key][0], dict):
                            print(f"       第一个元素的字段: {list(kg[key][0].keys())}")
                    else:
                        print(f"     - {key}: {type(kg[key]).__name__}")

if __name__ == "__main__":
    # 先深入检查数据结构
    inspect_data_structure()
    print("\n" + "="*60 + "\n")
    # 然后准备可视化数据
    prepare_visualization_data()