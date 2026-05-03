#!/usr/bin/env python3
"""
家庭教育短视频制作工具 - 可视化版
基于 parenting-video-maker skill 规范实现
"""

import os
import re
import json
import subprocess
import asyncio
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# API配置（预留接口，后期填写）
API_CONFIG = {
    "qwen_image": {
        "endpoint": "",
        "api_key": "",
        "model": "qwen-image-2.0"
    },
    "ace_music": {
        "endpoint": "",
        "api_key": ""
    },
    "tts": {
        "edge_tts": True,
        "custom_endpoint": "",
        "api_key": ""
    }
}

# TTS音色配置
TTS_VOICES = {
    "xiaoxiao": {"name": "晓晓", "voice": "zh-CN-XiaoxiaoNeural", "gender": "女"},
    "xiaoyi": {"name": "小艺", "voice": "zh-CN-XiaoyiNeural", "gender": "女"},
    "yunjian": {"name": "云健", "voice": "zh-CN-YunjianNeural", "gender": "男"},
    "yunxi": {"name": "云希", "voice": "zh-CN-YunxiNeural", "gender": "女"},
    "yunxia": {"name": "云夏", "voice": "zh-CN-YunxiaNeural", "gender": "女"},
    "yunyang": {"name": "云阳", "voice": "zh-CN-YunyangNeural", "gender": "男"},
    "luna": {"name": "露娜", "voice": "zh-CN-LunaNeural", "gender": "女"},
    "chengyu": {"name": "成宇", "voice": "zh-CN-ChengyuNeural", "gender": "男"}
}

# 选题模板
TOPICS = [
    "亲子沟通技巧",
    "情绪管理",
    "学习习惯培养",
    "自信心建立",
    "时间管理",
    "社交能力培养",
    "阅读习惯培养",
    "专注力提升"
]

# 语速选项
RATES = [
    ("很慢", "-20%"),
    ("慢", "-10%"),
    ("正常", "0%"),
    ("快", "+10%"),
    ("很快", "+20%"),
    ("极快", "+30%")
]

class ParentingVideoMaker:
    """家庭教育短视频制作器"""
    
    def __init__(self, api_config: Dict = None):
        self.output_dir = "output"
        self.images_dir = "images"
        self.subtitles_dir = "subtitles"
        self.audio_dir = "audio"
        self.api_config = api_config or API_CONFIG
        self._create_directories()
        self.progress_callback = None
        
    def _create_directories(self):
        for dir_name in [self.output_dir, self.images_dir, self.subtitles_dir, self.audio_dir]:
            os.makedirs(dir_name, exist_ok=True)
    
    def set_progress_callback(self, callback):
        self.progress_callback = callback
    
    def _update_progress(self, step, message, progress):
        if self.progress_callback:
            self.progress_callback(step, message, progress)
    
    def create_script(self, topic: str) -> Dict[str, str]:
        scripts = {
            "亲子沟通技巧": {
                "opening": "你是否有过这样的经历？孩子回家一声不吭，问什么都只说'没事'？或者你刚想和孩子聊聊，他却不耐烦地说'别管我'？据调查，超过70%的家长都面临着亲子沟通的困扰。",
                "content": "今天我要分享三个实用的沟通技巧，让你和孩子的对话更顺畅。第一个技巧：'情绪共鸣法'。当孩子闹脾气时，先别急着讲道理，而是说'我知道你现在很生气'，认可他的情绪，孩子才会愿意打开心扉。第二个技巧：'有限选择法'。与其问'你作业写完了吗'，不如说'你是想现在写作业，还是吃完点心后写'？给孩子选择权，他会更有参与感。第三个技巧：'特殊时光'。每天留出15分钟，专注陪孩子做他喜欢的事，不看手机，不批评，只享受彼此的陪伴。",
                "cta": "回顾一下今天的场景：当孩子情绪低落时，我们不再急于说教，而是先共鸣他的情绪；当孩子磨蹭时，我们用有限选择代替催促；当孩子需要关注时，我们用特殊时光建立连接。行动建议：从今天开始，选择一个技巧尝试，坚持一周，你会看到明显的变化。互动提问：你家孩子最让你头疼的沟通问题是什么？欢迎在评论区分享，我们一起讨论解决方法。价值升华：良好的亲子沟通不是天生的，而是需要学习和练习的。当我们用正确的方法与孩子交流，不仅能解决当下的问题，更能为孩子的一生奠定健康的人际关系基础。",
                "emotion": "warm positive"
            },
            "情绪管理": {
                "opening": "孩子动不动就发脾气？玩具摔一地？说两句就哭？其实这些都是孩子在表达情绪，只是他们还没学会正确的方式。",
                "content": "今天教你三个方法，帮助孩子学会管理情绪。第一，情绪命名。告诉孩子'我看到你现在很生气'，让他知道自己的感受叫什么。第二，冷静角落。在家设置一个安静的角落，放些孩子喜欢的书或玩具，让他情绪激动时可以去那里冷静。第三，深呼吸练习。和孩子一起做三次深呼吸，吸气四秒，呼气六秒，帮助他平复心情。",
                "cta": "今天学到的三个方法：情绪命名、冷静角落、深呼吸练习。行动建议：明天就和孩子一起练习深呼吸，坚持一周看看变化。互动提问：你家孩子情绪最激动的时候是什么场景？欢迎分享你的经验。价值升华：教会孩子管理情绪，不仅能让家庭更和谐，更能为他未来的人际关系和心理健康打下坚实基础。",
                "emotion": "calm reassuring"
            },
            "学习习惯培养": {
                "opening": "孩子写作业拖拉？注意力不集中？书桌乱七八糟？培养良好的学习习惯，比成绩更重要。",
                "content": "今天分享三个培养学习习惯的秘诀。第一，固定时间地点。每天在同一时间、同一地点写作业，让身体形成条件反射。第二，番茄工作法。学习25分钟，休息5分钟，提高专注力。第三，整理书桌。干净整洁的环境能让孩子更专心学习。",
                "cta": "总结一下：固定时间地点、番茄工作法、整理书桌。行动建议：今晚就和孩子一起整理书桌，制定明天的学习计划。互动提问：你家孩子在学习习惯上最大的挑战是什么？我们一起探讨解决方法。价值升华：良好的学习习惯能让孩子受益终身，不仅提高学习效率，更能培养自律和责任感。",
                "emotion": "encouraging positive"
            },
            "自信心建立": {
                "opening": "孩子总说'我不行'？遇到困难就退缩？其实每个孩子都有无限潜力，关键是如何培养他的自信心。",
                "content": "今天分享三个建立自信心的方法。第一，具体表扬。不说'你真棒'，而是说'你刚才很努力地完成了这个任务'。第二，让孩子自己做。给孩子一些力所能及的任务，让他体验成功的喜悦。第三，接受失败。告诉孩子失败是学习的机会，不是终点。",
                "cta": "今天学到的三个方法：具体表扬、独立完成、接受失败。行动建议：从明天开始，每天找一个机会表扬孩子的努力。互动提问：你家孩子在哪些方面最缺乏自信？我们一起想办法。价值升华：自信心是孩子成长的翅膀，有了它，孩子才能勇敢地飞向更高更远的地方。",
                "emotion": "inspirational hopeful"
            },
            "时间管理": {
                "opening": "孩子总是拖延？做事没有条理？时间管理能力是孩子一生的财富，从小培养至关重要。",
                "content": "今天分享三个时间管理技巧。第一，制定时间表。和孩子一起制定每天的计划，让他学会安排时间。第二，设置优先级。教孩子区分重要和紧急的事情。第三，使用计时器。帮助孩子建立时间观念。",
                "cta": "总结三个技巧：制定时间表、设置优先级、使用计时器。行动建议：今晚就和孩子一起制定明天的时间表。互动提问：你家孩子最容易拖延的事情是什么？我们一起讨论解决方法。价值升华：良好的时间管理能力能让孩子受益终身，让他成为时间的主人。",
                "emotion": "practical organized"
            },
            "社交能力培养": {
                "opening": "孩子在学校不合群？不敢和同学说话？社交能力是孩子融入社会的关键。",
                "content": "今天分享三个培养社交能力的方法。第一，角色扮演。在家模拟各种社交场景，让孩子练习如何与人交往。第二，鼓励分享。让孩子学会分享玩具和感受。第三，教孩子表达。告诉孩子如何用语言表达自己的想法和需求。",
                "cta": "今天学到的三个方法：角色扮演、学会分享、表达自己。行动建议：明天就和孩子玩一次角色扮演游戏。互动提问：你家孩子在社交方面最大的挑战是什么？欢迎分享。价值升华：良好的社交能力能让孩子拥有更多朋友，让他的成长之路更加快乐和顺利。",
                "emotion": "friendly warm"
            },
            "阅读习惯培养": {
                "opening": "孩子不爱读书？总是坐不住？培养阅读习惯能开阔孩子的视野，丰富他的内心世界。",
                "content": "今天分享三个培养阅读习惯的方法。第一，亲子共读。每天花15分钟和孩子一起读书，让阅读成为亲子时光。第二，选择合适的书。根据孩子的年龄和兴趣选择书籍。第三，营造阅读环境。在家设置一个舒适的阅读角。",
                "cta": "总结三个方法：亲子共读、选择好书、营造环境。行动建议：今晚就和孩子一起读一本他喜欢的书。互动提问：你家孩子最喜欢读什么类型的书？欢迎推荐。价值升华：阅读是孩子通往知识海洋的小船，让他在书的世界里自由探索和成长。",
                "emotion": "warm cozy"
            },
            "专注力提升": {
                "opening": "孩子注意力不集中？做事情容易分心？专注力是学习和生活的基础能力。",
                "content": "今天分享三个提升专注力的方法。第一，减少干扰。创造一个安静的学习环境，关闭电视和手机。第二，一次做一件事。教孩子专注于当前的任务，不要一心多用。第三，兴趣引导。从孩子感兴趣的事情开始，逐渐培养专注力。",
                "cta": "今天学到的三个方法：减少干扰、专注当下、兴趣引导。行动建议：明天开始，每次让孩子专注做一件事。互动提问：你家孩子做什么事情时最专注？我们一起探讨。价值升华：良好的专注力能让孩子事半功倍，在学习和生活中更加高效和成功。",
                "emotion": "calm focused"
            }
        }
        return scripts.get(topic, scripts["亲子沟通技巧"])
    
    def generate_storyboard(self, script: Dict[str, str]) -> List[Dict[str, Any]]:
        opening_parts = [p for p in script["opening"].split("？") if p.strip()]
        content_parts = [p for p in script["content"].split("。") if p.strip()]
        cta_parts = [p for p in script["cta"].split("。") if p.strip()]
        
        scenes = []
        for i, part in enumerate(opening_parts[:3]):
            scenes.append({
                "id": i + 1,
                "type": "类型1" if i == 0 else "类型2",
                "duration": 5 if i == 0 else 4,
                "description": f"开场钩子：{part.strip()}",
                "prompt": self._generate_prompt("类型1" if i == 0 else "类型2", part.strip()),
                "golden_line": ""
            })
        
        for i, part in enumerate(content_parts[:5]):
            scenes.append({
                "id": len(scenes) + 1,
                "type": "类型1" if i % 2 == 0 else "类型4",
                "duration": 6 if i % 2 == 0 else 5,
                "description": f"核心干货{i+1}：{part.strip()}",
                "prompt": self._generate_prompt("类型1" if i % 2 == 0 else "类型4", part.strip()),
                "golden_line": self._extract_golden_line(part)
            })
        
        for i, part in enumerate(cta_parts[:4]):
            scenes.append({
                "id": len(scenes) + 1,
                "type": "类型1",
                "duration": 6 if i < 2 else 8,
                "description": f"CTA{i+1}：{part.strip()}",
                "prompt": self._generate_prompt("类型1", part.strip()),
                "golden_line": self._extract_golden_line(part) if i == 3 else ""
            })
        
        return scenes
    
    def _generate_prompt(self, scene_type: str, description: str) -> str:
        instructor = "Female family education instructor, 35 years old, brown bob hair, amber eyes, round friendly face, delicate gold wire glasses, light purple cardigan over white blouse"
        boy = "7-year-old Chinese boy, short dark brown hair, deep brown eyes, round face, light blue cartoon T-shirt, dark shorts"
        girl = "8-year-old Chinese girl, shoulder-length black hair, bright dark eyes, round face, light pink cartoon T-shirt, denim skirt"
        
        prompts = {
            "类型1": f"{instructor} — Professional warm setting, home office, bookshelf with parenting books, soft lighting, speaking confidently",
            "类型2": f"{boy} — {description}, home setting, natural lighting, emotional expression",
            "类型3": "Cozy home interior, warm lighting, educational posters, comfortable sofa, no people",
            "类型4": f"{instructor}, {girl} — Parent child interaction, warm home setting, caring expressions",
            "类型5": "Close up of child's hands doing activity, focused expression, warm lighting",
            "类型6": "Abstract educational infographic style, soft colors, growth metaphor, no text"
        }
        return prompts.get(scene_type, prompts["类型1"])
    
    def _extract_golden_line(self, text: str) -> str:
        keywords = ["技巧", "方法", "秘诀", "重要", "关键", "学会", "培养", "坚持"]
        for keyword in keywords:
            idx = text.find(keyword)
            if idx != -1:
                end = text.find("，", idx)
                if end == -1:
                    end = text.find("。", idx)
                if end == -1:
                    end = len(text)
                result = text[idx:end].strip()
                if len(result) <= 18:
                    return result
        return ""
    
    def generate_subtitles(self, script: Dict[str, str]) -> Dict[str, Any]:
        full_text = script["opening"] + script["content"] + script["cta"]
        filtered_text = self._filter_punctuation(full_text)
        narrator_lines = self._smart_split(filtered_text)
        timestamps = self._assign_timestamps(narrator_lines)
        
        golden_line = self._find_main_golden_line(script)
        golden_lines = self._make_golden_subtitle(golden_line)
        
        return {
            "golden": {"text": golden_lines, "start": 10.0, "end": 14.0},
            "narrator": timestamps
        }
    
    def _filter_punctuation(self, text: str) -> str:
        return re.sub(r'[^\u4e00-\u9fff\w\s？！：]', '', text)
    
    def _smart_split(self, text: str, max_chars: int = 12) -> List[str]:
        def is_cjk(c):
            return '\u4e00' <= c <= '\u9fff'
        
        lines = []
        i = 0
        while i < len(text):
            if len(text) - i <= max_chars:
                lines.append(text[i:])
                break
            
            end = i + max_chars
            best = end
            
            for offset in range(max_chars - 1):
                idx = end - 1 - offset
                if idx <= i:
                    break
                if is_cjk(text[idx - 1]) and is_cjk(text[idx]):
                    best = idx
                    break
            
            lines.append(text[i:best])
            i = best
            while i < len(text) and text[i] in ' \t':
                i += 1
        
        return lines
    
    def _assign_timestamps(self, lines: List[str]) -> List[Dict[str, Any]]:
        timestamps = []
        current_time = 0.0
        
        for line in lines:
            duration = min(len(line) * 0.25 + 0.5, 3.5)
            timestamps.append({
                "text": line,
                "start": round(current_time, 2),
                "end": round(current_time + duration, 2)
            })
            current_time += duration
        
        return timestamps
    
    def _make_golden_subtitle(self, text: str, max_chars: int = 9) -> List[str]:
        text = re.sub(r'[\u3010\u3011]', '', text).strip()
        lines = []
        while len(text) > max_chars:
            lines.append(text[:max_chars])
            text = text[max_chars:]
        if text:
            lines.append(text)
        return lines[:2]
    
    def _find_main_golden_line(self, script: Dict[str, str]) -> str:
        content = script["content"]
        keywords = ["技巧", "方法", "秘诀", "重要", "关键"]
        
        for keyword in keywords:
            idx = content.find(keyword)
            if idx != -1:
                start = max(0, idx - 5)
                end = content.find("。", idx)
                if end == -1:
                    end = content.find("，", idx)
                if end == -1:
                    end = len(content)
                return content[start:end].strip()
        
        return "良好的教育需要耐心和方法"
    
    async def generate_tts(self, text: str, voice_name: str = "xiaoxiao", rate: str = "+10%") -> str:
        try:
            import edge_tts
            voice = TTS_VOICES.get(voice_name, TTS_VOICES["xiaoxiao"])
            output_path = os.path.join(self.audio_dir, "voiceover.mp3")
            
            communicate = edge_tts.Communicate(text, voice["voice"], rate=rate)
            await communicate.save(output_path)
            
            return output_path
        except ImportError:
            return ""
        except Exception as e:
            return ""
    
    def generate_images(self, storyboard: List[Dict[str, Any]]) -> List[str]:
        image_paths = []
        
        for scene in storyboard:
            image_path = os.path.join(self.images_dir, f"scene{scene['id']}.png")
            
            if self.api_config["qwen_image"]["endpoint"]:
                pass
            else:
                self._create_placeholder_image(image_path, scene)
            
            image_paths.append(image_path)
        
        return image_paths
    
    def _create_placeholder_image(self, path: str, scene: Dict[str, Any]):
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', (1536, 2688), color=(240, 240, 240))
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype('arial.ttf', 40)
            except:
                font = ImageFont.load_default()
            
            text = f"Scene {scene['id']}\n{scene['type']}\n{scene['description'][:30]}..."
            lines = text.split('\n')
            y = 800
            
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                width = bbox[2] - bbox[0]
                draw.text(((1536 - width) // 2, y), line, fill='black', font=font)
                y += 60
            
            img.save(path)
        except ImportError:
            pass
    
    def synthesize_video(self, image_paths: List[str], audio_path: str, subtitles: Dict[str, Any]) -> str:
        output_path = os.path.join(self.output_dir, "final_with_audio.mp4")
        
        if not os.path.exists(audio_path):
            return ""
        
        try:
            list_path = os.path.join(self.output_dir, "images.txt")
            with open(list_path, 'w', encoding='utf-8') as f:
                for img_path in image_paths:
                    if os.path.exists(img_path):
                        f.write(f"file '{os.path.abspath(img_path)}'\n")
                        f.write("duration 5\n")
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", list_path,
                "-i", audio_path,
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                "-vf", "scale=720:1280",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return output_path if result.returncode == 0 else ""
                
        except FileNotFoundError:
            return ""
        except Exception as e:
            return ""
    
    def generate_cover(self, storyboard: List[Dict[str, Any]], title: str, subtitle: str):
        cover_path = os.path.join(self.output_dir, "cover.png")
        
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
            
            first_image_path = os.path.join(self.images_dir, f"scene1.png")
            
            if os.path.exists(first_image_path):
                canvas = Image.open(first_image_path)
            else:
                canvas = Image.new('RGB', (720, 1280), color=(50, 50, 50))
            
            canvas = canvas.resize((720, 1280))
            canvas = canvas.filter(ImageFilter.GaussianBlur(15))
            canvas = Image.blend(canvas, Image.new("RGB", (720, 1280), (0, 0, 0)), 0.35)
            
            draw = ImageDraw.Draw(canvas)
            
            try:
                title_font = ImageFont.truetype('arial.ttf', 64)
                subtitle_font = ImageFont.truetype('arial.ttf', 32)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
            
            title_text = title[:16]
            title_lines = self._wrap_text(title_text, 8)
            
            y = 400
            for line in title_lines:
                bbox = draw.textbbox((0, 0), line, font=title_font)
                width = bbox[2] - bbox[0]
                draw.text(((720 - width) // 2, y), line, fill=(255, 215, 0), font=title_font)
                y += 80
            
            subtitle_text = subtitle[:18]
            bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            width = bbox[2] - bbox[0]
            draw.text(((720 - width) // 2, y + 20), subtitle_text, fill=(200, 200, 200), font=subtitle_font)
            
            canvas.save(cover_path)
        except ImportError:
            pass
    
    def _wrap_text(self, text: str, max_chars: int) -> List[str]:
        lines = []
        while len(text) > max_chars:
            lines.append(text[:max_chars])
            text = text[max_chars:]
        if text:
            lines.append(text)
        return lines
    
    def generate_delivery_list(self, topic: str, script: Dict[str, str], 
                               storyboard: List[Dict[str, Any]], subtitles: Dict[str, Any]) -> str:
        delivery = {
            "选题": topic,
            "脚本": script,
            "分镜数量": len(storyboard),
            "分镜摘要": [{k: v for k, v in s.items() if k != 'prompt'} for s in storyboard],
            "字幕示例": subtitles["narrator"][:5],
            "金句": subtitles["golden"],
            "标题方案": [
                f"三招搞定{topic}，让孩子更优秀",
                f"{topic}的秘密武器，家长必看",
                f"从困惑到精通，{topic}只需这三步"
            ],
            "发布简介": f"你家孩子{topic}方面有困扰吗？今天分享三个超实用的{topic}技巧，简单易操作，坚持一周就能看到效果。快来试试吧！评论区分享你的经验，我们一起讨论。#亲子教育 #家庭教育 #育儿技巧",
            "标签": ["#亲子教育", "#家庭教育", "#育儿技巧", "#亲子沟通", "#家长课堂"],
            "视频文件": "output/final_with_audio.mp4",
            "封面文件": "output/cover.png",
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        delivery_path = os.path.join(self.output_dir, "delivery清单.json")
        with open(delivery_path, 'w', encoding='utf-8') as f:
            json.dump(delivery, f, ensure_ascii=False, indent=2)
        
        return delivery_path
    
    async def run(self, topic: str = "亲子沟通技巧", voice_name: str = "xiaoxiao", 
                  rate: str = "+10%") -> Dict[str, Any]:
        
        self._update_progress(1, "创建脚本...", 10)
        script = self.create_script(topic)
        
        self._update_progress(2, "生成分镜...", 20)
        storyboard = self.generate_storyboard(script)
        
        self._update_progress(3, "生成字幕...", 30)
        subtitles = self.generate_subtitles(script)
        
        self._update_progress(4, "生成图片...", 40)
        image_paths = self.generate_images(storyboard)
        
        self._update_progress(5, "生成配音...", 55)
        full_text = script["opening"] + script["content"] + script["cta"]
        audio_path = await self.generate_tts(full_text, voice_name, rate)
        
        self._update_progress(6, "合成视频...", 75)
        video_path = ""
        if audio_path:
            video_path = self.synthesize_video(image_paths, audio_path, subtitles)
        
        self._update_progress(7, "生成封面...", 90)
        self.generate_cover(storyboard, topic, "让亲子关系更亲密")
        
        self._update_progress(8, "生成交付清单...", 95)
        delivery_path = self.generate_delivery_list(topic, script, storyboard, subtitles)
        
        self._update_progress(9, "完成！", 100)
        
        return {
            "success": True,
            "topic": topic,
            "voice": voice_name,
            "rate": rate,
            "video_path": video_path,
            "delivery_path": delivery_path
        }

class VideoMakerGUI:
    """可视化界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("家庭教育短视频制作工具")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        self.maker = ParentingVideoMaker()
        self.maker.set_progress_callback(self.update_progress)
        
        self.selected_topic = tk.StringVar()
        self.selected_voice = tk.StringVar()
        self.selected_rate = tk.StringVar()
        self.current_progress = tk.IntVar()
        self.progress_text = tk.StringVar()
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="家庭教育短视频制作工具", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # 配置面板
        config_frame = ttk.LabelFrame(main_frame, text="配置选项", padding="10")
        config_frame.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        # 选题选择
        ttk.Label(config_frame, text="选题主题：").grid(row=0, column=0, sticky=tk.W, pady=5)
        topic_combo = ttk.Combobox(config_frame, textvariable=self.selected_topic, 
                                   values=TOPICS, width=20)
        topic_combo.current(0)
        topic_combo.grid(row=0, column=1, padx=10)
        
        # 音色选择
        ttk.Label(config_frame, text="配音音色：").grid(row=1, column=0, sticky=tk.W, pady=5)
        voice_combo = ttk.Combobox(config_frame, textvariable=self.selected_voice,
                                   values=[v["name"] for v in TTS_VOICES.values()], width=20)
        voice_combo.current(0)
        voice_combo.grid(row=1, column=1, padx=10)
        
        # 语速选择
        ttk.Label(config_frame, text="语速：").grid(row=2, column=0, sticky=tk.W, pady=5)
        rate_combo = ttk.Combobox(config_frame, textvariable=self.selected_rate,
                                  values=[r[0] for r in RATES], width=20)
        rate_combo.current(3)
        rate_combo.grid(row=2, column=1, padx=10)
        
        # 预览面板
        preview_frame = ttk.LabelFrame(main_frame, text="预览与内容", padding="10")
        preview_frame.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 脚本预览
        script_label = ttk.Label(preview_frame, text="脚本预览：")
        script_label.grid(row=0, column=0, sticky=tk.W)
        
        self.script_text = tk.Text(preview_frame, height=15, width=50)
        self.script_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        
        # 进度面板
        progress_frame = ttk.LabelFrame(main_frame, text="制作进度", padding="10")
        progress_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.current_progress, 
                                            maximum=100, length=800)
        self.progress_bar.grid(row=0, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_text)
        self.progress_label.grid(row=1, column=0, padx=10, pady=5)
        
        # 日志面板
        log_frame = ttk.LabelFrame(main_frame, text="制作日志", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky=(tk.W, tk.E))
        main_frame.rowconfigure(3, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, width=100)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 按钮面板
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.preview_btn = ttk.Button(button_frame, text="预览脚本", command=self.preview_script)
        self.preview_btn.grid(row=0, column=0, padx=10)
        
        self.start_btn = ttk.Button(button_frame, text="开始制作", command=self.start_making)
        self.start_btn.grid(row=0, column=1, padx=10)
        
        self.open_btn = ttk.Button(button_frame, text="打开输出目录", command=self.open_output)
        self.open_btn.grid(row=0, column=2, padx=10)
        
        self.current_progress.set(0)
        self.progress_text.set("准备就绪")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_progress(self, step, message, progress):
        self.current_progress.set(progress)
        self.progress_text.set(f"步骤 {step}/9: {message}")
        self.log(message)
        self.root.update_idletasks()
    
    def preview_script(self):
        topic = self.selected_topic.get()
        script = self.maker.create_script(topic)
        
        self.script_text.delete(1.0, tk.END)
        self.script_text.insert(tk.END, "【开场钩子】\n")
        self.script_text.insert(tk.END, script["opening"] + "\n\n")
        self.script_text.insert(tk.END, "【核心干货】\n")
        self.script_text.insert(tk.END, script["content"] + "\n\n")
        self.script_text.insert(tk.END, "【CTA引导】\n")
        self.script_text.insert(tk.END, script["cta"])
        
        self.log(f"已加载选题: {topic}")
    
    def start_making(self):
        self.start_btn.config(state=tk.DISABLED)
        self.current_progress.set(0)
        self.log_text.delete(1.0, tk.END)
        
        topic = self.selected_topic.get()
        voice_name = None
        for key, value in TTS_VOICES.items():
            if value["name"] == self.selected_voice.get():
                voice_name = key
                break
        
        rate_value = None
        for name, rate in RATES:
            if name == self.selected_rate.get():
                rate_value = rate
                break
        
        self.log(f"开始制作视频: {topic}")
        self.log(f"配置: {self.selected_voice.get()} / {self.selected_rate.get()}")
        
        def run_task():
            try:
                result = asyncio.run(self.maker.run(topic, voice_name, rate_value))
                if result["success"]:
                    self.log("视频制作完成！")
                    self.log(f"输出目录: {self.maker.output_dir}")
                    messagebox.showinfo("成功", "视频制作完成！\n\n输出文件:\n- output/final_with_audio.mp4\n- output/cover.png\n- output/delivery清单.json")
                else:
                    self.log("视频制作失败")
                    messagebox.showerror("错误", "视频制作失败，请检查日志")
            except Exception as e:
                self.log(f"制作过程出错: {str(e)}")
                messagebox.showerror("错误", f"制作过程出错: {str(e)}")
            finally:
                self.start_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=run_task, daemon=True).start()
    
    def open_output(self):
        if os.path.exists(self.maker.output_dir):
            subprocess.run(["explorer", self.maker.output_dir], shell=True)
        else:
            messagebox.showinfo("提示", "输出目录不存在，请先制作视频")

def main():
    root = tk.Tk()
    app = VideoMakerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
