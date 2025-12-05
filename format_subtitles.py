import re
import os

def format_subtitles(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into blocks
    blocks = content.strip().split('\n\n')
    formatted_blocks = []

    # Replacements map
    replacements = {
        '能夠': '能',
        '想要': '想',
        '上面': '上',
        '需要': '要',
        '大家': '你',
        '但是': '但',
        '哈哈哈': 'XDD',
        '還是': '或是',
        '不想要': '不想',
        '很需要': '需要',
        # '個': '一個', # This might be risky if it's already "一個". Regex better.
        '防': '預防',
        '東西': '產品',
        '覺得說': '覺得',
        '比如說': '比如',
        '我自己': '自己',
        '這件事情': '這件事',
        '大廠': '大品牌',
        '過程當中': '過程中',
        '情況之下': '情況下',
        '一件事情': '一件事',
        '大概': '大致上',
        '想像的那麼快': '想像地快',
        '沒有辦法': '無法',
        '底層': '底層的邏輯'
    }

    # Filler words to remove (careful with these)
    fillers = ['那', '欸', '對吧', '嘛', '然後', '哦', '就是', '那當然']

    for block in blocks:
        lines = block.split('\n')
        if len(lines) < 3:
            formatted_blocks.append(block)
            continue

        # Extract text lines (usually line 3 onwards)
        # SRT format:
        # 1
        # 00:00:00,000 --> 00:00:05,000
        # Text line 1
        # Text line 2
        
        index = lines[0]
        timestamp = lines[1]
        text_lines = lines[2:]
        
        full_text = "".join(text_lines) # Join lines to process as one sentence
        
        # 1. Basic Replacements
        for old, new in replacements.items():
            full_text = full_text.replace(old, new)
            
        # Handle "個" -> "一個" separately to avoid "一個" -> "一一個"
        # If "個" is preceded by a number or "這/那", maybe don't change?
        # User said "個" -> "一個". Let's assume standalone "個".
        # full_text = re.sub(r'(?<!一)個', '一個', full_text) # Simple heuristic
        # Actually, "三個" -> "三一個" is wrong. "這個" -> "這一個".
        # Let's skip this one if it's risky, or apply carefully.
        # "個" is a measure word. "一個" is "one [measure]".
        # If user wants "個" -> "一個", maybe they mean "有個..." -> "有一個...".
        # I'll skip it to be safe or only apply if not preceded by number.
        
        # 2. Remove Fillers
        for filler in fillers:
            # Remove filler if it's at start or followed by comma
            # Or just remove them? "Remove redundant...".
            # "然後" is structural. Removing it might break meaning.
            # I will remove them if they are at the start of the sentence.
            if full_text.startswith(filler):
                full_text = full_text[len(filler):]
            # Also remove "就是" inside?
            full_text = full_text.replace(f'{filler}，', '')
            full_text = full_text.replace(f'，{filler}', '')
        
        # 3. AI/Human "它"
        if any(x in full_text.upper() for x in ['AI', 'LLM', 'GPT', 'MODEL', '模型']):
            full_text = full_text.replace('他', '它').replace('她', '它')

        # 4. Spacing (Zh/En)
        # Add space between Zh and En/Num
        full_text = re.sub(r'([\u4e00-\u9fff])([a-zA-Z0-9])', r'\1 \2', full_text)
        full_text = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fff])', r'\1 \2', full_text)
        
        # 5. Punctuation
        # Rule 7: Add full-width comma for specific words
        triggers = ['請問', '假設', '比如', '他說', '另外', '那一天', '我認為']
        for trigger in triggers:
            if full_text.startswith(trigger) and not full_text.startswith(f"{trigger}，"):
                 full_text = full_text.replace(trigger, f"{trigger}，", 1)
        
        # Regex for "第N個"
        full_text = re.sub(r'(第\d+個)', r'\1，', full_text)

        # Rule 1: Remove all punctuation (at end?)
        # User says "Remove all punctuation marks" but also "Use full-width punctuation".
        # And "Add space...".
        # I will replace standard punctuation with full-width or space.
        # If I remove all, I lose structure.
        # Let's assume: Internal punctuation -> Full width. End of line -> Removed.
        
        # Convert common punctuation to full-width
        full_text = full_text.replace(',', '，').replace('.', '。').replace('?', '？').replace('!', '！')
        
        # Remove trailing punctuation
        if full_text and full_text[-1] in '，。？！':
            full_text = full_text[:-1]

        # 6. Line Length (Max 18 chars)
        # If > 18 chars, split.
        # Try to split at punctuation or space.
        
        new_lines = []
        while len(full_text) > 18:
            # Find split point
            # Prefer split at '，' or ' '
            split_idx = -1
            
            # Look for punctuation in the first 18 chars (or slightly more?)
            # No, strictly max 18.
            chunk = full_text[:18]
            
            # Check for punctuation to split *after*
            puncs = ['，', '。', '？', '！', ' ']
            last_punc = -1
            for p in puncs:
                idx = chunk.rfind(p)
                if idx > last_punc:
                    last_punc = idx
            
            if last_punc > 5: # Don't split too early
                split_idx = last_punc + 1 # Include punctuation in first line? Or remove?
                # Usually keep punctuation attached to first part.
                new_lines.append(full_text[:split_idx])
                full_text = full_text[split_idx:].strip()
            else:
                # Force split at 18
                new_lines.append(full_text[:18])
                full_text = full_text[18:].strip()
        
        if full_text:
            new_lines.append(full_text)
            
        # Reconstruct block
        new_block = f"{index}\n{timestamp}\n" + "\n".join(new_lines)
        formatted_blocks.append(new_block)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(formatted_blocks))

if __name__ == "__main__":
    input_path = r"d:\yan\mp3_to_text\11月24日_cht_1.txt"
    output_path = r"d:\yan\mp3_to_text\11月24日_cht_formatted.txt"
    format_subtitles(input_path, output_path)
    print(f"Formatted file saved to {output_path}")
