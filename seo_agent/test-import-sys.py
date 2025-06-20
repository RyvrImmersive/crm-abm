import sys
print("Python path:", sys.path)

try:
    import keyword_research
    print("Module imported successfully")
    print("Module contents:", dir(keyword_research))
    print("Has get_keyword_ideas_for_langflow?", hasattr(keyword_research, 'get_keyword_ideas_for_langflow'))
except Exception as e:
    print(f"Import error: {e}")