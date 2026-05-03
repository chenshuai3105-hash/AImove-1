#!/usr/bin/env python3
"""
家庭教育短视频制作工具
基于 parenting-video-maker skill 规范实现
"""

import os
import re
import json
import subprocess
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

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
        "edge_tts": True,  # 使用edge-tts本地引擎
        "custom_endpoint": "",
        "api_key": ""
    }
}

# TTS音色配置
TTS_VOICES = {
    "xiaoxiao": {"name": "晓晓", "voice": "zh-CN-XiaoxiaoNeural", "gender": "female"},
    "xiaoyi": {"name": "小艺", "voice": "zh-CN-XiaoyiNeural", "gender": "female"},
    "yunjian": {"name": "云健", "voice": "zh-CN-YunjianNeural", "gender": "male"},
    "yunxi": {"name": "云希", "voice": "zh-CN-YunxiNeural", "gender": "female"},
    "yunxia": {"name": "云夏", "voice": "zh-CN-YunxiaNeural", "gender": "female"},
    "yunyang": {"name": "云阳", "voice": "zh-CN-YunyangNeural", "gender": "male"},
    "luna": {"name": "露娜", "voice": "zh-CN-LunaNeural", "gender": "female"},
    "chengyu": {"name": "成宇", "voice": "zh-CN-ChengyuNeural", "gender": "male"}
}

class ParentingVideoMaker:
    """家庭教育短视频制作器"""
    
    def __init__(self, api_config: Dict = None):
        self.output_dir = "output"
        self.images_dir = "images"
        self.subtitles_dir = "subtitles"
        self.audio_dir = "audio"
        self.api_config = api_config or API_CONFIG
        self._create_directories()
        
    def _create_directories(self):
        """创建必要的目录结构"""
        for dir_name in [self.output_dir, self.images_dir, self.subtitles_dir, self.audio_dir]:
            os.makedirs(dir_name, exist_ok=True)
    
    def create_script(self, topic: str) -> Dict[str, str]:
        """
        创建短视频脚本
        :param topic: 选题主题
        :return: 包含开场、干货、CTA的脚本字典
        """
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
        """
        生成分镜脚本
        :param script: 脚本字典
        :return: 分镜列表
        """
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
        """生成图片生成提示词"""
        instructor = "Female family education instructor, 35 years old, brown bob hair, amber eyes, round friendly face, delicate gold wire glasses, light purple cardigan over white blouse"
        boy = "7-year-old Chinese boy, short dark brown hair, deep brown eyes, round face, light blue cartoon T-shirt, dark shorts"
        girl = "8-year-old Chinese girl, shoulder-length black hair, bright dark eyes, round face, light pink cartoon T-shirt, denim skirt"
        
        prompts = {
            "类型1": f"{instructor} — Professional warm setting, home office, bookshelf with parenting books, soft lighting, speaking confidently, educational atmosphere",
            "类型2": f"{boy} — {description}, home setting, natural lighting, emotional expression, realistic scene",
            "类型3": "Cozy home interior, warm lighting, educational posters on wall, comfortable sofa, bookshelf, no people",
            "类型4": f"{instructor}, {girl} — Parent child interaction, warm home setting, caring expressions, natural lighting, educational activity",
            "类型5": "Close up of child's hands doing activity, focused expression, warm lighting, educational context",
            "类型6": "Abstract educational infographic style, soft colors, growth metaphor, glowing light, no text"
        }
        
        return prompts.get(scene_type, prompts["类型1"])
    
    def _extract_golden_line(self, text: str) -> str:
        """从文本中提取金句"""
        keywords = ["技巧", "方法", "秘诀", "重要", "关键", "学会", "培养", "坚持", "自信", "沟通", "习惯"]
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
        """
        生成字幕
        :param script: 脚本字典
        :return: 包含金句和旁白的字幕字典
        """
        full_text = script["opening"] + script["content"] + script["cta"]
        filtered_text = self._filter_punctuation(full_text)
        narrator_lines = self._smart_split(filtered_text)
        timestamps = self._assign_timestamps(narrator_lines)
        
        golden_line = self._find_main_golden_line(script)
        golden_lines = self._make_golden_subtitle(golden_line)
        
        return {
            "golden": {
                "text": golden_lines,
                "start": 10.0,
                "end": 14.0
            },
            "narrator": timestamps
        }
    
    def _filter_punctuation(self, text: str) -> str:
        """仅保留问号、感叹号和冒号"""
        return re.sub(r'[^\u4e00-\u9fff\w\s？！：]', '', text)
    
    def _smart_split(self, text: str, max_chars: int = 12) -> List[str]:
        """智能断句"""
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
        """分配时间戳"""
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
        """生成金句字幕"""
        text = re.sub(r'[\u3010\u3011]', '', text).strip()
        lines = []
        
        while len(text) > max_chars:
            lines.append(text[:max_chars])
            text = text[max_chars:]
        
        if text:
            lines.append(text)
        
        return lines[:2]
    
    def _find_main_golden_line(self, script: Dict[str, str]) -> str:
        """找到主要金句"""
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
    
    async def generate_tts(self, text: str, voice_name: str = "xiaoxiao", 
                          rate: str = "+10%") -> str:
        """
        使用edge-tts生成配音
        :param text: 配音文本
        :param voice_name: 音色名称
        :param rate: 语速
        :return: 音频文件路径
        """
        try:
            import edge_tts
            
            voice = TTS_VOICES.get(voice_name, TTS_VOICES["xiaoxiao"])
            output_path = os.path.join(self.audio_dir, "voiceover.mp3")
            
            communicate = edge_tts.Communicate(text, voice["voice"], rate=rate)
            await communicate.save(output_path)
            
            print(f"[TTS] 配音生成成功: {output_path}")
            return output_path
        except ImportError:
            print("[TTS] edge-tts未安装，跳过配音生成")
            return ""
        except Exception as e:
            print(f"[TTS] 配音生成失败: {e}")
            return ""
    
    def generate_images(self, storyboard: List[Dict[str, Any]]) -> List[str]:
        """
        生成图片（预留API接口）
        :param storyboard: 分镜列表
        :return: 图片路径列表
        """
        image_paths = []
        
        for scene in storyboard:
            image_path = os.path.join(self.images_dir, f"scene{scene['id']}.png")
            
            # 预留Qwen Image API调用接口
            if self.api_config["qwen_image"]["endpoint"]:
                # 实际API调用代码（后期实现）
                print(f"[IMAGE] 调用Qwen API生成图片: scene{scene['id']}")
                # response = requests.post(
                #     self.api_config["qwen_image"]["endpoint"],
                #     headers={"Authorization": f"Bearer {self.api_config['qwen_image']['api_key']}"},
                #     json={"prompt": scene["prompt"], "size": "1536*2688"}
                # )
                # with open(image_path, 'wb') as f:
                #     f.write(response.content)
            else:
                # 生成占位图片
                self._create_placeholder_image(image_path, scene)
            
            image_paths.append(image_path)
        
        return image_paths
    
    def _create_placeholder_image(self, path: str, scene: Dict[str, Any]):
        """创建占位图片"""
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
            print(f"[IMAGE] 生成占位图片: {path}")
        except ImportError:
            print("[IMAGE] PIL未安装，跳过图片生成")
    
    def generate_bgm(self, emotion: str = "warm positive") -> str:
        """
        生成背景音乐（预留API接口）
        :param emotion: 情感基调
        :return: BGM文件路径
        """
        bgm_path = os.path.join(self.audio_dir, "bgm.mp3")
        
        if self.api_config["ace_music"]["endpoint"]:
            print(f"[BGM] 调用ACE Music API生成背景音乐: {emotion}")
            # 实际API调用代码（后期实现）
        else:
            print("[BGM] 未配置音乐API，跳过BGM生成")
            return ""
        
        return bgm_path
    
    def synthesize_video(self, image_paths: List[str], audio_path: str, 
                        subtitles: Dict[str, Any], duration: float = 60.0) -> str:
        """
        使用FFmpeg合成视频
        :param image_paths: 图片路径列表
        :param audio_path: 音频路径
        :param subtitles: 字幕数据
        :param duration: 视频时长
        :return: 输出视频路径
        """
        output_path = os.path.join(self.output_dir, "final_with_audio.mp4")
        
        if not os.path.exists(audio_path):
            print("[FFMPEG] 音频文件不存在，跳过视频合成")
            return ""
        
        try:
            # 生成图片列表文件
            list_path = os.path.join(self.output_dir, "images.txt")
            with open(list_path, 'w', encoding='utf-8') as f:
                for img_path in image_paths:
                    if os.path.exists(img_path):
                        f.write(f"file '{os.path.abspath(img_path)}'\n")
                        f.write("duration 5\n")
            
            # 生成视频命令
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
            
            if result.returncode == 0:
                print(f"[FFMPEG] 视频合成成功: {output_path}")
                return output_path
            else:
                print(f"[FFMPEG] 视频合成失败: {result.stderr}")
                return ""
                
        except FileNotFoundError:
            print("[FFMPEG] ffmpeg未安装，跳过视频合成")
            return ""
        except Exception as e:
            print(f"[FFMPEG] 视频合成异常: {e}")
            return ""
    
    def generate_cover(self, storyboard: List[Dict[str, Any]], title: str, subtitle: str):
        """生成封面图"""
        cover_path = os.path.join(self.output_dir, "cover.png")
        
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
            
            # 使用第一个分镜图片作为背景
            first_image_path = os.path.join(self.images_dir, f"scene1.png")
            
            if os.path.exists(first_image_path):
                canvas = Image.open(first_image_path)
            else:
                canvas = Image.new('RGB', (720, 1280), color=(50, 50, 50))
            
            # 调整尺寸
            canvas = canvas.resize((720, 1280))
            
            # 模糊和暗化
            canvas = canvas.filter(ImageFilter.GaussianBlur(15))
            canvas = Image.blend(canvas, Image.new("RGB", (720, 1280), (0, 0, 0)), 0.35)
            
            # 添加文字
            draw = ImageDraw.Draw(canvas)
            
            try:
                title_font = ImageFont.truetype('arial.ttf', 64)
                subtitle_font = ImageFont.truetype('arial.ttf', 32)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
            
            # 主标题
            title_text = title[:16]
            title_lines = self._wrap_text(title_text, 8)
            
            y = 400
            for line in title_lines:
                bbox = draw.textbbox((0, 0), line, font=title_font)
                width = bbox[2] - bbox[0]
                draw.text(((720 - width) // 2, y), line, fill=(255, 215, 0), font=title_font)
                y += 80
            
            # 副标题
            subtitle_text = subtitle[:18]
            bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            width = bbox[2] - bbox[0]
            draw.text(((720 - width) // 2, y + 20), subtitle_text, fill=(200, 200, 200), font=subtitle_font)
            
            canvas.save(cover_path)
            print(f"[COVER] 封面生成成功: {cover_path}")
            
        except ImportError:
            print("[COVER] PIL未安装，跳过封面生成")
    
    def _wrap_text(self, text: str, max_chars: int) -> List[str]:
        """文本换行"""
        lines = []
        while len(text) > max_chars:
            lines.append(text[:max_chars])
            text = text[max_chars:]
        if text:
            lines.append(text)
        return lines
    
    def generate_delivery_list(self, topic: str, script: Dict[str, str], 
                               storyboard: List[Dict[str, Any]], subtitles: Dict[str, Any]) -> str:
        """生成交付清单"""
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
        """
        执行完整的视频制作流程
        :param topic: 选题主题
        :param voice_name: TTS音色名称
        :param rate: 语速
        :return: 制作结果
        """
        print(f"[INFO] 开始制作家庭教育短视频：{topic}")
        print(f"[INFO] 音色: {TTS_VOICES[voice_name]['name']}, 语速: {rate}")
        print("=" * 60)
        
        # Step 1: 创建脚本
        print("[STEP 1/6] 创建脚本...")
        script = self.create_script(topic)
        total_chars = len(script["opening"] + script["content"] + script["cta"])
        print(f"  ✓ 脚本创建完成，总字数: {total_chars}")
        
        # Step 2: 生成分镜
        print("[STEP 2/6] 生成分镜...")
        storyboard = self.generate_storyboard(script)
        print(f"  ✓ 分镜生成完成，共 {len(storyboard)} 个镜头")
        
        # Step 3: 生成字幕
        print("[STEP 3/6] 生成字幕...")
        subtitles = self.generate_subtitles(script)
        print(f"  ✓ 字幕生成完成，共 {len(subtitles['narrator'])} 条旁白")
        print(f"  ✓ 金句: {subtitles['golden']['text']}")
        
        # Step 4: 生成图片
        print("[STEP 4/6] 生成图片...")
        image_paths = self.generate_images(storyboard)
        print(f"  ✓ 图片生成完成，共 {len(image_paths)} 张")
        
        # Step 5: TTS配音
        print("[STEP 5/6] 生成配音...")
        full_text = script["opening"] + script["content"] + script["cta"]
        audio_path = await self.generate_tts(full_text, voice_name, rate)
        
        # Step 6: 合成视频
        print("[STEP 6/6] 合成视频...")
        if audio_path:
            video_path = self.synthesize_video(image_paths, audio_path, subtitles)
        else:
            video_path = ""
        
        # 生成封面
        print("[STEP 7/7] 生成封面...")
        self.generate_cover(storyboard, topic, "让亲子关系更亲密")
        
        # 生成交付清单
        delivery_path = self.generate_delivery_list(topic, script, storyboard, subtitles)
        print(f"  ✓ 交付清单已保存: {delivery_path}")
        
        print("=" * 60)
        print("[INFO] 视频制作流程完成！")
        
        return {
            "success": True,
            "topic": topic,
            "voice": voice_name,
            "rate": rate,
            "script": script,
            "storyboard": storyboard,
            "subtitles": subtitles,
            "audio_path": audio_path,
            "video_path": video_path,
            "delivery_path": delivery_path
        }

def main():
    """主函数"""
    maker = ParentingVideoMaker()
    
    print("=" * 60)
    print("      家庭教育短视频制作工具")
    print("=" * 60)
    
    # 选题选择
    topics = list(maker.create_script.__doc__.__contains__) if hasattr(maker.create_script.__doc__, '__contains__') else \
             ["亲子沟通技巧", "情绪管理", "学习习惯培养", "自信心建立", "时间管理", 
              "社交能力培养", "阅读习惯培养", "专注力提升"]
    
    print("\n【选题列表】")
    for i, topic in enumerate(topics, 1):
        print(f"{i:2d}. {topic}")
    
    while True:
        try:
            choice = int(input("\n请输入选题编号: "))
            if 1 <= choice <= len(topics):
                selected_topic = topics[choice - 1]
                break
            print("请输入有效编号！")
        except ValueError:
            print("请输入数字！")
    
    # 音色选择
    print("\n【音色选择】")
    for i, (key, value) in enumerate(TTS_VOICES.items(), 1):
        print(f"{i:2d}. {value['name']} ({value['gender']})")
    
    while True:
        try:
            voice_choice = int(input("请输入音色编号: "))
            if 1 <= voice_choice <= len(TTS_VOICES):
                selected_voice = list(TTS_VOICES.keys())[voice_choice - 1]
                break
            print("请输入有效编号！")
        except ValueError:
            print("请输入数字！")
    
    # 语速选择
    rates = ["-20%", "-10%", "0%", "+10%", "+20%", "+30%"]
    print("\n【语速选择】")
    for i, rate in enumerate(rates, 1):
        desc = "很慢" if i == 1 else "慢" if i == 2 else "正常" if i == 3 else \
               "快" if i == 4 else "很快" if i == 5 else "极快"
        print(f"{i:2d}. {rate} ({desc})")
    
    while True:
        try:
            rate_choice = int(input("请输入语速编号: "))
            if 1 <= rate_choice <= len(rates):
                selected_rate = rates[rate_choice - 1]
                break
            print("请输入有效编号！")
        except ValueError:
            print("请输入数字！")
    
    # 执行制作流程
    print("\n" + "=" * 60)
    print(f"开始制作: {selected_topic}")
    print(f"音色: {TTS_VOICES[selected_voice]['name']}, 语速: {selected_rate}")
    print("=" * 60)
    
    asyncio.run(maker.run(selected_topic, selected_voice, selected_rate))
    
    print("\n制作完成！输出文件:")
    print(f"  - 交付清单: output/delivery清单.json")
    print(f"  - 视频文件: output/final_with_audio.mp4")
    print(f"  - 封面图片: output/cover.png")

if __name__ == "__main__":
    main()