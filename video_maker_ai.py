#!/usr/bin/env python3
"""
家庭教育短视频制作工具 - 大模型对接版
集成 MiniMax Token Plan（文本+语音+音乐）和 Qwen-image-2.0（图像）API
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
from tkinter import ttk, messagebox, scrolledtext

# API配置（请在API配置窗口中填写）
API_CONFIG = {
    "minimax": {
        "api_key": "",
        "is_token_plan": True,
        "text_model": "MiniMax-M2.7",
        "speech_model": "speech-2.8-hd",
        "music_model": "Music-2.0"
    },
    "qwen_image": {
        "api_key": "",
        "model": "qwen-image-2.0"
    }
}

# MiniMax语音合成音色（Token Plan支持的中文音色）
MINIMAX_VOICES = {
    "aixia": {"name": "艾夏", "voice_id": "Aixia", "language": "Chinese"},
    "aoyun": {"name": "奥云", "voice_id": "AoYun", "language": "Chinese"},
    "baobei": {"name": "宝贝", "voice_id": "BaoBei", "language": "Chinese"},
    "daming": {"name": "大明", "voice_id": "DaMing", "language": "Chinese"},
    "dandan": {"name": "丹丹", "voice_id": "DanDan", "language": "Chinese"},
    "fanfan": {"name": "凡凡", "voice_id": "FanFan", "language": "Chinese"},
    "feifei": {"name": "菲菲", "voice_id": "FeiFei", "language": "Chinese"},
    "ganggang": {"name": "刚刚", "voice_id": "GangGang", "language": "Chinese"},
    "guoguo": {"name": "果果", "voice_id": "GuoGuo", "language": "Chinese"},
    "haiyan": {"name": "海燕", "voice_id": "HaiYan", "language": "Chinese"},
    "hengheng": {"name": "恒恒", "voice_id": "HengHeng", "language": "Chinese"},
    "honghong": {"name": "红红", "voice_id": "HongHong", "language": "Chinese"},
    "huahua": {"name": "花花", "voice_id": "HuaHua", "language": "Chinese"},
    "huilin": {"name": "慧琳", "voice_id": "HuiLin", "language": "Chinese"},
    "jianjian": {"name": "健健", "voice_id": "JianJian", "language": "Chinese"},
    "jingjing": {"name": "静静", "voice_id": "JingJing", "language": "Chinese"},
    "junjun": {"name": "军军", "voice_id": "JunJun", "language": "Chinese"},
    "keke": {"name": "可可", "voice_id": "KeKe", "language": "Chinese"},
    "lele": {"name": "乐乐", "voice_id": "LeLe", "language": "Chinese"},
    "linlin": {"name": "琳琳", "voice_id": "LinLin", "language": "Chinese"}
}

class MiniMaxConnector:
    """MiniMax Token Plan API连接器"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    async def chat_completion(self, prompt: str, max_tokens: int = 2000) -> str:
        """调用MiniMax文本生成API（Token Plan - Anthropic风格）"""
        api_key = self.config["minimax"]["api_key"]
        
        if not api_key:
            print("[DEBUG] 未配置API Key，使用模拟数据")
            return None
        
        try:
            import aiohttp
            import time
            
            url = "https://api.minimax.chat/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": self.config["minimax"]["text_model"],
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位专业的家庭教育指导师，擅长为25-40岁家长提供实用的教育建议。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": False,
                "bot_setting": [
                    {
                        "bot_name": "Assistant",
                        "content": "你是一位专业的家庭教育指导师，擅长为25-40岁家长提供实用的教育建议。"
                    }
                ],
                "reply_constraints": {
                    "sender_type": "user",
                    "sender_name": "User"
                }
            }
            
            max_retries = 5  # 增加重试次数
            retry_delay = 10  # 增加初始等待时间
            
            for attempt in range(max_retries):
                try:
                    timeout = aiohttp.ClientTimeout(total=120)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(url, headers=headers, json=data) as response:
                            status_code = response.status
                            print(f"[DEBUG] API响应状态码: {status_code} (尝试 {attempt + 1}/{max_retries})")
                            
                            if status_code == 529:
                                print(f"[WARNING] 请求拥挤(529)，等待 {retry_delay}秒后重试...")
                                await asyncio.sleep(retry_delay)
                                retry_delay = min(retry_delay * 2, 45)  # 最多等待45秒
                                continue  # 继续下一次重试
                                
                            if status_code != 200:
                                error_text = await response.text()
                                print(f"[ERROR] API调用失败，状态码: {status_code}，响应: {error_text[:200]}")
                                if attempt < max_retries - 1:
                                    print(f"[DEBUG] 等待 {retry_delay}秒后重试...")
                                    await asyncio.sleep(retry_delay)
                                    retry_delay = min(retry_delay * 2, 45)
                                    continue
                                else:
                                    print("[ERROR] 所有重试都失败，使用模拟数据")
                                    return None
                            
                            try:
                                result = await response.json()
                            except Exception as json_error:
                                error_text = await response.text()
                                print(f"[ERROR] JSON解析失败: {json_error}，原始响应: {error_text[:200]}")
                                if attempt < max_retries - 1:
                                    print(f"[DEBUG] 等待 {retry_delay}秒后重试...")
                                    await asyncio.sleep(retry_delay)
                                    retry_delay *= 2
                                    continue
                                else:
                                    print("[ERROR] 所有重试都失败，使用模拟数据")
                                    return None
                            
                            print(f"[DEBUG] API响应: {str(result)[:300]}")
                            
                            if "choices" in result and result["choices"]:
                                content = result["choices"][0]["message"]["content"]
                                print(f"[DEBUG] 提取内容长度: {len(content)}")
                                
                                # 去除 <think> 标签
                                import re
                                content = re.sub(r'<think>[\s\S]*?</think>', '', content)
                                content = content.strip()
                                print(f"[DEBUG] 去除think标签后长度: {len(content)}")
                                
                                return content
                        
                        print("[ERROR] API响应中没有choices字段")
                        if attempt < max_retries - 1:
                            print(f"[DEBUG] 等待 {retry_delay}秒后重试...")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        else:
                            print("[ERROR] 所有重试都失败，使用模拟数据")
                            return None
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"[DEBUG] 请求异常，继续重试: {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        print("[ERROR] 所有重试都失败，使用模拟数据")
                        return None
            
            print("[ERROR] 所有重试都失败了")
            return None
        except Exception as e:
            print(f"[ERROR] MiniMax文本API调用失败: {str(e)}")
            return None
    
    def _mock_response(self, prompt: str) -> str:
        """模拟响应"""
        if "选题" in prompt:
            topics = [
                {"title": "亲子沟通技巧：如何让孩子愿意跟你说话", "score": 92, "reason": "选题贴近家长痛点，内容实用"},
                {"title": "情绪管理：帮助孩子学会控制情绪", "score": 88, "reason": "需求广泛，教育意义强"},
                {"title": "学习习惯培养：让孩子爱上学习", "score": 85, "reason": "家长关注度高，市场需求大"}
            ]
            return json.dumps(topics, ensure_ascii=False)
        elif "脚本" in prompt:
            topic = "亲子沟通技巧"
            if "情绪管理" in prompt:
                topic = "情绪管理"
            elif "学习习惯" in prompt:
                topic = "学习习惯培养"
            
            scripts = {
                "亲子沟通技巧": {
                    "opening": "你是否有过这样的经历？孩子回家一声不吭，问什么都只说'没事'？或者你刚想和孩子聊聊，他却不耐烦地说'别管我'？据调查，超过70%的家长都面临着亲子沟通的困扰。",
                    "content": "今天我要分享三个实用的沟通技巧，让你和孩子的对话更顺畅。第一个技巧：'情绪共鸣法'。当孩子闹脾气时，先别急着讲道理，而是说'我知道你现在很生气'，认可他的情绪，孩子才会愿意打开心扉。第二个技巧：'有限选择法'。与其问'你作业写完了吗'，不如说'你是想现在写作业，还是吃完点心后写'？给孩子选择权，他会更有参与感。第三个技巧：'特殊时光'。每天留出15分钟，专注陪孩子做他喜欢的事，不看手机，不批评，只享受彼此的陪伴。",
                    "cta": "回顾一下今天的场景：当孩子情绪低落时，我们不再急于说教，而是先共鸣他的情绪；当孩子磨蹭时，我们用有限选择代替催促；当孩子需要关注时，我们用特殊时光建立连接。行动建议：从今天开始，选择一个技巧尝试，坚持一周，你会看到明显的变化。互动提问：你家孩子最让你头疼的沟通问题是什么？欢迎在评论区分享，我们一起讨论解决方法。价值升华：良好的亲子沟通不是天生的，而是需要学习和练习的。当我们用正确的方法与孩子交流，不仅能解决当下的问题，更能为孩子的一生奠定健康的人际关系基础。"
                },
                "情绪管理": {
                    "opening": "孩子动不动就发脾气？玩具摔一地？说两句就哭？其实这些都是孩子在表达情绪，只是他们还没学会正确的方式。",
                    "content": "今天教你三个方法，帮助孩子学会管理情绪。第一，情绪命名。告诉孩子'我看到你现在很生气'，让他知道自己的感受叫什么。第二，冷静角落。在家设置一个安静的角落，放些孩子喜欢的书或玩具，让他情绪激动时可以去那里冷静。第三，深呼吸练习。和孩子一起做三次深呼吸，吸气四秒，呼气六秒，帮助他平复心情。",
                    "cta": "今天学到的三个方法：情绪命名、冷静角落、深呼吸练习。行动建议：明天就和孩子一起练习深呼吸，坚持一周看看变化。互动提问：你家孩子情绪最激动的时候是什么场景？欢迎分享你的经验。价值升华：教会孩子管理情绪，不仅能让家庭更和谐，更能为他未来的人际关系和心理健康打下坚实基础。"
                },
                "学习习惯培养": {
                    "opening": "孩子写作业拖拉？注意力不集中？书桌乱七八糟？培养良好的学习习惯，比成绩更重要。",
                    "content": "今天分享三个培养学习习惯的秘诀。第一，固定时间地点。每天在同一时间、同一地点写作业，让身体形成条件反射。第二，番茄工作法。学习25分钟，休息5分钟，提高专注力。第三，整理书桌。干净整洁的环境能让孩子更专心学习。",
                    "cta": "总结一下：固定时间地点、番茄工作法、整理书桌。行动建议：今晚就和孩子一起整理书桌，制定明天的学习计划。互动提问：你家孩子在学习习惯上最大的挑战是什么？我们一起探讨解决方法。价值升华：良好的学习习惯能让孩子受益终身，不仅提高学习效率，更能培养自律和责任感。"
                }
            }
            return json.dumps(scripts[topic], ensure_ascii=False)
        elif "字幕" in prompt:
            subtitles = {
                "narrator": [
                    {"text": "你是否有过这样的经历", "start": 0.0, "end": 2.5},
                    {"text": "孩子回家一声不吭", "start": 2.5, "end": 4.5},
                    {"text": "问什么都只说没事", "start": 4.5, "end": 6.5},
                    {"text": "或者你刚想和孩子聊聊", "start": 6.5, "end": 8.5},
                    {"text": "他却不耐烦地说别管我", "start": 8.5, "end": 10.5}
                ],
                "golden": {"text": ["良好的亲子沟通", "需要学习和练习"], "start": 10.0, "end": 14.0}
            }
            return json.dumps(subtitles, ensure_ascii=False)
        return ""
    
    async def speech_synthesis(self, text: str, voice_id: str = "Aixia", rate: float = 1.0) -> str:
        """调用MiniMax语音合成API（Token Plan）"""
        api_key = self.config["minimax"]["api_key"]
        
        if not api_key:
            return self._mock_tts(text)
        
        try:
            import aiohttp
            
            url = "https://api.minimax.chat/v1/t2a/sync"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "text": text,
                "model": self.config["minimax"]["speech_model"],
                "voice_setting": {
                    "voice_id": voice_id,
                    "language": "Chinese",
                    "rate": rate,
                    "pitch": 0,
                    "volume": 1.0
                },
                "output_format": "mp3"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        output_path = "audio/voiceover.mp3"
                        with open(output_path, 'wb') as f:
                            f.write(audio_data)
                        return output_path
                    else:
                        print(f"语音合成失败: {response.status}")
                        return ""
        except Exception as e:
            print(f"MiniMax语音API调用失败: {e}")
            return self._mock_tts(text)
    
    def _mock_tts(self, text: str) -> str:
        """模拟TTS"""
        try:
            import edge_tts
            output_path = "audio/voiceover.mp3"
            asyncio.run(edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural", rate="+10%").save(output_path))
            return output_path
        except:
            return ""
    
    async def generate_image(self, prompt: str, size: str = "1080*1920") -> str:
        """调用MiniMax图像生成API（Token Plan image-01）"""
        api_key = self.config["minimax"]["api_key"]
        
        if not api_key:
            print("[IMAGE] 未配置MiniMax API")
            return ""
        
        try:
            import aiohttp
            
            url = "https://api.minimaxi.com/v1/image_generation"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            width, height = map(int, size.split('*'))
            data = {
                "model": "image-01",
                "prompt": prompt,
                "width": width,
                "height": height,
                "n": 1,
                "output_format": "url"
            }
            
            print(f"[IMAGE] 请求: {prompt[:50]}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    status_code = response.status
                    print(f"[IMAGE] 状态码: {status_code}")
                    
                    if status_code != 200:
                        error_text = await response.text()
                        print(f"[IMAGE] 错误: {error_text}")
                        return ""
                    
                    result = await response.json()
                    print(f"[IMAGE] 响应完整内容:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
                    if "status_code" in result:
                        if result["status_code"] == 0:
                            if "result" in result:
                                results = result["result"]
                                if isinstance(results, list) and len(results) > 0:
                                    first_result = results[0]
                                    if "url" in first_result and first_result["url"]:
                                        image_url = first_result["url"]
                                        print(f"[IMAGE] 下载图片: {image_url[:50]}...")
                                        async with session.get(image_url) as img_response:
                                            image_data = await img_response.read()
                                            print(f"[IMAGE] 图片大小: {len(image_data)} bytes")
                                            if len(image_data) < 1000:
                                                print(f"[IMAGE] 图片数据太小，可能是空图片")
                                                return ""
                                            image_path = f"images/img_{hash(prompt) % 10000}.png"
                                            with open(image_path, 'wb') as f:
                                                f.write(image_data)
                                            print(f"[IMAGE] 保存成功: {image_path}")
                                            return image_path
                                    else:
                                        print(f"[IMAGE] result中没有url字段: {first_result.keys()}")
                        else:
                            print(f"[IMAGE] API错误码: {result['status_code']}")
                            if "status_msg" in result:
                                print(f"[IMAGE] 错误信息: {result['status_msg']}")
                    
                    if "base_resp" in result and result["base_resp"].get("status_code") == 0:
                        if "data" in result and result["data"]:
                            if "image_urls" in result["data"] and isinstance(result["data"]["image_urls"], list) and len(result["data"]["image_urls"]) > 0:
                                image_url = result["data"]["image_urls"][0]
                                print(f"[IMAGE] 下载图片: {image_url[:60]}...")
                                async with session.get(image_url) as img_response:
                                    image_data = await img_response.read()
                                    print(f"[IMAGE] 图片大小: {len(image_data)} bytes")
                                    if len(image_data) < 1000:
                                        print(f"[IMAGE] 图片数据太小，可能是空图片")
                                        return ""
                                    import time
                                    image_path = f"images/img_{int(time.time() * 1000)}_{hash(prompt) % 1000}.png"
                                    with open(image_path, 'wb') as f:
                                        f.write(image_data)
                                    print(f"[IMAGE] 保存成功: {image_path}")
                                    return image_path
                            elif "image_url" in result["data"] and result["data"]["image_url"]:
                                image_url = result["data"]["image_url"]
                                print(f"[IMAGE] 下载图片: {image_url[:60]}...")
                                async with session.get(image_url) as img_response:
                                    image_data = await img_response.read()
                                    print(f"[IMAGE] 图片大小: {len(image_data)} bytes")
                                    if len(image_data) < 1000:
                                        print(f"[IMAGE] 图片数据太小，可能是空图片")
                                        return ""
                                    import time
                                    image_path = f"images/img_{int(time.time() * 1000)}_{hash(prompt) % 1000}.png"
                                    with open(image_path, 'wb') as f:
                                        f.write(image_data)
                                    print(f"[IMAGE] 保存成功: {image_path}")
                                    return image_path
                            elif "image" in result["data"] and result["data"]["image"]:
                                print(f"[IMAGE] 解码base64图片...")
                                import base64
                                image_data = base64.b64decode(result["data"]["image"])
                                print(f"[IMAGE] 图片大小: {len(image_data)} bytes")
                                if len(image_data) < 1000:
                                    print(f"[IMAGE] 图片数据太小，可能是空图片")
                                    return ""
                                import time
                                image_path = f"images/img_{int(time.time() * 1000)}_{hash(prompt) % 1000}.png"
                                with open(image_path, 'wb') as f:
                                    f.write(image_data)
                                print(f"[IMAGE] 保存成功: {image_path}")
                                return image_path
                            else:
                                print(f"[IMAGE] 响应数据中没有找到 image_urls、image_url 或 image 字段")
                                print(f"[IMAGE] data 内容: {json.dumps(result['data'], indent=2)}")
                    else:
                        if "base_resp" in result:
                            print(f"[IMAGE] API错误: {result['base_resp'].get('status_msg', '未知错误')}")
                        else:
                            print(f"[IMAGE] 响应格式不正确")
                    return ""
        except Exception as e:
            print(f"MiniMax图像API调用失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    async def generate_storyboard(self, script: dict) -> str:
        """调用MiniMax文本生成API生成分镜脚本"""
        api_key = self.config["minimax"]["api_key"]
        
        if not api_key:
            print("[STORYBOARD] 未配置MiniMax API，使用本地生成分镜")
            return ""
        
        try:
            import aiohttp
            
            url = "https://api.minimax.chat/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            full_script = script.get("opening", "") + "\n" + \
                          script.get("content", "") + "\n" + \
                          script.get("cta", "")
            
            prompt = f"""根据以下视频脚本，为家庭教育短视频生成分镜脚本：

脚本内容：
{full_script}

角色描述：
- 指导师：Female family education instructor, 35 years old, brown bob hair, amber eyes, round friendly face, delicate gold wire glasses, light purple cardigan over white blouse
- 男孩：7-year-old Chinese boy, short dark brown hair, deep brown eyes, round face, light blue cartoon T-shirt, dark shorts
- 女孩：8-year-old Chinese girl, shoulder-length black hair, bright dark eyes, round face, light pink cartoon T-shirt, denim skirt

镜头类型说明：
- 类型1：指导师出镜讲解（半身/全身）-> 开场、讲解、总结
- 类型2：案例场景（孩子+指导师或单独孩子）-> 中段高潮、情感共鸣
- 类型3：纯场景（无人物）-> 过渡、情绪转换
- 类型4：真实交互场景（家庭/校园/社交）-> 展示孩子与父母、老师或同学朋友的真实互动实景
- 类型5：特写细节（手、表情、物体）-> 情绪放大
- 类型6：概念插画与视觉隐喻 -> 使用视觉隐喻或无字信息图表风格

要求：
1. 【强制要求】分镜数量至少5个（开场钩子+核心干货各要点+CTA引导）
2. 【强制要求】每个分镜时长严格控制在4-9秒之间
3. 【语速标准】按180字/分钟（3字/秒）计算时长
4. 【内容匹配】每个分镜的画面描述必须与对应口播内容强相关
5. 【金句提取】智能提取：只有真正有价值、有冲击力的句子才作为金句
   - 金句标准：有概括性、有记忆点、能引发共鸣（如包含数字、反问、对比等）
   - 允许某些分镜没有金句（golden_line字段可为空字符串）
   - 整个视频建议有1-3条高质量金句即可
6. 直接输出JSON格式，不要有思考过程和额外文字

输出格式：
{{
    "scenes": [
        {{
            "id": 1,
            "type": "类型1",
            "duration": 5,
            "description_cn": "中文描述",
            "prompt_en": "英文图片提示词",
            "golden_line": "该镜头对应的金句（没有则为空字符串）"
        }}
    ],
    "golden_lines": ["视频中所有金句的汇总列表"]
}}"""
            
            data = {
                "model": self.config["minimax"]["text_model"],
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位专业的短视频分镜设计师，擅长为家庭教育视频设计专业分镜脚本。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 3000,
                "temperature": 0.7,
                "stream": False
            }
            
            print(f"[STORYBOARD] 调用MiniMax API生成分镜...")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "choices" in result and result["choices"]:
                            content = result["choices"][0]["message"]["content"]
                            print(f"[STORYBOARD] 分镜生成成功，内容长度: {len(content)}")
                            return content
                    else:
                        error_text = await response.text()
                        print(f"[STORYBOARD] API调用失败: {error_text[:200]}")
                        return ""
        except Exception as e:
            print(f"[STORYBOARD] MiniMax分镜API调用失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    async def generate_music(self, emotion: str = "warm positive", duration: int = 60) -> str:
        """调用MiniMax音乐生成API（Token Plan music-2.6 纯音乐模式）"""
        api_key = self.config["minimax"]["api_key"]
        
        if not api_key:
            print("[MUSIC] 未配置MiniMax API，跳过背景音乐生成")
            return ""
        
        try:
            import aiohttp
            import time
            
            url = "https://api.minimaxi.com/v1/music_generation"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": "music-2.6",
                "prompt": f"{emotion} background music for family education video, gentle piano melody, soft strings, hopeful and warm mood, instrumental, peaceful and calm",
                "is_instrumental": True,
                "duration": duration,
                "output_format": "url"
            }
            
            print(f"[MUSIC] 请求数据: {json.dumps(data, indent=2)[:500]}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    status_code = response.status
                    print(f"[MUSIC] 响应状态码: {status_code}")
                    
                    if status_code != 200:
                        error_text = await response.text()
                        print(f"[MUSIC] 错误响应: {error_text}")
                        return ""
                    
                    result = await response.json()
                    print(f"[MUSIC] 响应内容: {json.dumps(result, indent=2)[:1500]}")
                    
                    if "base_resp" in result and result["base_resp"].get("status_code") == 0:
                        if "data" in result and result["data"]:
                            if result["data"].get("audio_url"):
                                music_url = result["data"]["audio_url"]
                                print(f"[MUSIC] 下载音频: {music_url[:60]}...")
                                async with session.get(music_url) as music_response:
                                    music_data = await music_response.read()
                                    print(f"[MUSIC] 音频大小: {len(music_data)} bytes")
                                    music_path = "audio/bgm.mp3"
                                    with open(music_path, 'wb') as f:
                                        f.write(music_data)
                                    print(f"[MUSIC] 保存成功: {music_path}")
                                    return music_path
                            elif result["data"].get("audio"):
                                audio_value = result["data"]["audio"]
                                if audio_value.startswith("http"):
                                    print(f"[MUSIC] audio字段是URL，下载音频: {audio_value[:60]}...")
                                    async with session.get(audio_value) as music_response:
                                        music_data = await music_response.read()
                                        print(f"[MUSIC] 音频大小: {len(music_data)} bytes")
                                        music_path = "audio/bgm.mp3"
                                        with open(music_path, 'wb') as f:
                                            f.write(music_data)
                                        print(f"[MUSIC] 保存成功: {music_path}")
                                        return music_path
                                else:
                                    print(f"[MUSIC] 解码base64音频...")
                                    import base64
                                    audio_data = base64.b64decode(audio_value)
                                    print(f"[MUSIC] 音频大小: {len(audio_data)} bytes")
                                    music_path = "audio/bgm.mp3"
                                    with open(music_path, 'wb') as f:
                                        f.write(audio_data)
                                    print(f"[MUSIC] 保存成功: {music_path}")
                                    return music_path
                            elif result["data"].get("task_id"):
                                task_id = result["data"]["task_id"]
                                print(f"[MUSIC] 音乐生成任务已创建: {task_id}")
                                return await self._poll_music_task(session, task_id, api_key)
                            elif "audio_urls" in result["data"] and isinstance(result["data"]["audio_urls"], list) and len(result["data"]["audio_urls"]) > 0:
                                music_url = result["data"]["audio_urls"][0]
                                print(f"[MUSIC] 下载音频: {music_url[:60]}...")
                                async with session.get(music_url) as music_response:
                                    music_data = await music_response.read()
                                    print(f"[MUSIC] 音频大小: {len(music_data)} bytes")
                                    music_path = "audio/bgm.mp3"
                                    with open(music_path, 'wb') as f:
                                        f.write(music_data)
                                    print(f"[MUSIC] 保存成功: {music_path}")
                                    return music_path
                            else:
                                print(f"[MUSIC] 响应数据中没有找到音频字段")
                                print(f"[MUSIC] data 内容: {json.dumps(result['data'], indent=2)}")
                    else:
                        if "base_resp" in result:
                            print(f"[MUSIC] API错误: {result['base_resp'].get('status_msg', '未知错误')}")
                    return ""
        except Exception as e:
            print(f"MiniMax音乐API调用失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    async def _poll_music_task(self, session, task_id, api_key):
        """轮询音乐生成任务状态"""
        url = f"https://api.minimaxi.com/v1/music_generation/task/{task_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        for _ in range(30):
            try:
                async with session.get(url, headers=headers) as response:
                    result = await response.json()
                    print(f"[MUSIC] 任务状态: {json.dumps(result, indent=2)[:500]}")
                    
                    if "base_resp" in result and result["base_resp"].get("status_code") == 0:
                        if "data" in result and result["data"]:
                            if result["data"].get("status") == "completed":
                                if result["data"].get("audio_url"):
                                    music_url = result["data"]["audio_url"]
                                    async with session.get(music_url) as music_response:
                                        music_data = await music_response.read()
                                        music_path = "audio/bgm.mp3"
                                        with open(music_path, 'wb') as f:
                                            f.write(music_data)
                                        return music_path
                                elif result["data"].get("audio"):
                                    audio_value = result["data"]["audio"]
                                    if audio_value.startswith("http"):
                                        async with session.get(audio_value) as music_response:
                                            music_data = await music_response.read()
                                            music_path = "audio/bgm.mp3"
                                            with open(music_path, 'wb') as f:
                                                f.write(music_data)
                                            return music_path
                                    else:
                                        import base64
                                        audio_data = base64.b64decode(audio_value)
                                        music_path = "audio/bgm.mp3"
                                        with open(music_path, 'wb') as f:
                                            f.write(audio_data)
                                        return music_path
                            elif result["data"].get("status") == "failed":
                                print(f"[MUSIC] 任务失败")
                                return ""
                    
                    await asyncio.sleep(3)
            except Exception as e:
                print(f"[MUSIC] 轮询失败: {e}")
                await asyncio.sleep(3)
        
        print("[MUSIC] 轮询超时")
        return ""

class QwenImageConnector:
    """Qwen Image 2.0 API连接器"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    async def generate_image(self, prompt: str, size: str = "1080*1920") -> str:
        """调用Qwen图像生成API"""
        api_key = self.config["qwen_image"]["api_key"]
        
        if not api_key:
            return self._mock_image(prompt, size)
        
        try:
            import aiohttp
            
            url = "https://dashscope.aliyuncs.com/api/text2image"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": self.config["qwen_image"]["model"],
                "input": {
                    "prompt": prompt
                },
                "parameters": {
                    "size": size,
                    "n": 1
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    if "output" in result and result["output"].get("images"):
                        image_url = result["output"]["images"][0]
                        async with session.get(image_url) as img_response:
                            image_data = await img_response.read()
                            image_path = f"images/{hash(prompt) % 10000}.png"
                            with open(image_path, 'wb') as f:
                                f.write(image_data)
                        return image_path
                    return ""
        except Exception as e:
            print(f"Qwen图像API调用失败: {e}")
            return self._mock_image(prompt, size)
    
    def _mock_image(self, prompt: str, size: str = "1080*1920") -> str:
        """模拟生成图片（支持自定义尺寸）"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            width, height = map(int, size.split('*'))
            
            img = Image.new('RGB', (width, height), color=(240, 240, 240))
            draw = ImageDraw.Draw(img)
            
            font_size = int(min(width, height) / 40)
            try:
                font = ImageFont.truetype('arial.ttf', font_size)
            except:
                font = ImageFont.load_default()
            
            lines = []
            text = prompt[:150]
            max_chars_per_line = max(10, width // (font_size * 2))
            while text:
                lines.append(text[:max_chars_per_line])
                text = text[max_chars_per_line:]
            
            y = height // 3
            for line in lines[:6]:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                draw.text(((width - text_width) // 2, y), line, fill='black', font=font)
                y += font_size + 10
            
            image_path = f"images/{hash(prompt) % 10000}.png"
            img.save(image_path)
            return image_path
        except Exception as e:
            print(f"模拟图片生成失败: {e}")
            return ""

class StoryboardGenerator:
    """分镜生成器"""
    
    @staticmethod
    def generate(script: Dict[str, str]) -> List[Dict[str, Any]]:
        opening_parts = [p for p in script["opening"].split("？") if p.strip()]
        content_parts = [p for p in script["content"].split("。") if p.strip()]
        cta_parts = [p for p in script["cta"].split("。") if p.strip()]
        
        scenes = []
        instructor = "Female family education instructor, 35 years old, brown bob hair, amber eyes, round friendly face, delicate gold wire glasses, light purple cardigan over white blouse"
        boy = "7-year-old Chinese boy, short dark brown hair, deep brown eyes, round face, light blue cartoon T-shirt, dark shorts"
        girl = "8-year-old Chinese girl, shoulder-length black hair, bright dark eyes, round face, light pink cartoon T-shirt, denim skirt"
        
        for i, part in enumerate(opening_parts[:3]):
            scene_type = "类型1" if i == 0 else "类型2"
            prompts = {
                "类型1": f"{instructor} — Professional warm home office setting, bookshelf with parenting books, soft lighting, speaking confidently to camera, educational atmosphere",
                "类型2": f"{boy} — Child coming home from school with sad expression, standing in living room, natural home lighting, realistic scene"
            }
            
            scenes.append({
                "id": i + 1,
                "type": scene_type,
                "duration": 5 if i == 0 else 4,
                "description_cn": f"开场钩子：{part.strip()}",
                "prompt_en": prompts[scene_type],
                "golden_line": ""
            })
        
        for i, part in enumerate(content_parts[:5]):
            scene_type = "类型1" if i % 2 == 0 else "类型4"
            prompts = {
                "类型1": f"{instructor} — Explaining educational concept, warm lighting, professional setting, expressive hand gestures, engaging expression",
                "类型4": f"{instructor}, {girl} — Parent child interaction scene, warm home setting, caring expressions, educational activity, natural lighting"
            }
            
            scenes.append({
                "id": len(scenes) + 1,
                "type": scene_type,
                "duration": 6 if i % 2 == 0 else 5,
                "description_cn": f"核心干货{i+1}：{part.strip()}",
                "prompt_en": prompts[scene_type],
                "golden_line": StoryboardGenerator._extract_golden_line(part)
            })
        
        for i, part in enumerate(cta_parts[:4]):
            scenes.append({
                "id": len(scenes) + 1,
                "type": "类型1",
                "duration": 6 if i < 2 else 8,
                "description_cn": f"CTA{i+1}：{part.strip()}",
                "prompt_en": f"{instructor} — Summarizing and giving advice, warm and encouraging expression, professional setting, soft lighting",
                "golden_line": StoryboardGenerator._extract_golden_line(part) if i == 3 else ""
            })
        
        return scenes
    
    @staticmethod
    def _extract_golden_line(text: str) -> str:
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

class VideoComposer:
    """视频合成器"""
    
    @staticmethod
    def synthesize(image_paths: List[str], audio_path: str, bgm_path: str = "", subtitles: dict = None, output_path: str = "output/final_with_audio.mp4", width: int = 720, height: int = 1280, subtitle_scale: float = 0.55, subtitle_settings: dict = None) -> bool:
        os.makedirs("output", exist_ok=True)
        with open("output/ffmpeg_debug.log", "w", encoding="utf-8") as log_file:
            log_file.write(f"[FFMPEG DEBUG] image_paths count: {len(image_paths)}\n")
            log_file.write(f"[FFMPEG DEBUG] audio_path: {audio_path}\n")
            log_file.write(f"[FFMPEG DEBUG] audio_exists: {os.path.exists(audio_path)}\n")
            
            if not os.path.exists(audio_path):
                log_file.write("[FFMPEG DEBUG] 音频文件不存在\n")
                return False
            
            try:
                audio_duration = VideoComposer._get_audio_duration(audio_path)
                log_file.write(f"[FFMPEG DEBUG] audio_duration: {audio_duration}\n")
                image_duration = max(audio_duration, len(image_paths) * 5)
                log_file.write(f"[FFMPEG DEBUG] image_duration: {image_duration}\n")
                
                list_path = "output/images.txt"
                valid_images = []
                with open(list_path, 'w', encoding='utf-8') as f:
                    for i, img_path in enumerate(image_paths):
                        if os.path.exists(img_path):
                            abs_path = os.path.abspath(img_path)
                            f.write(f"file '{abs_path}'\n")
                            duration = max(2, image_duration / len(image_paths))
                            f.write(f"duration {duration}\n")
                            valid_images.append(img_path)
                        else:
                            log_file.write(f"[FFMPEG DEBUG] 图片不存在: {img_path}\n")
                
                if not valid_images:
                    log_file.write("[FFMPEG DEBUG] 没有有效的图片文件\n")
                    return False
                
                audio_inputs = ["-i", audio_path]
                audio_count = 1
                
                if bgm_path and os.path.exists(bgm_path):
                    audio_inputs.extend(["-i", bgm_path])
                    audio_count = 2
                    filter_complex = ["-filter_complex", "[1:a]volume=1.0[a1];[2:a]volume=0.3[a2];[a1][a2]amix=inputs=2[a]"]
                    map_args = ["-map", "0:v", "-map", "[a]"]
                else:
                    filter_complex = []
                    map_args = ["-map", "0:v", "-map", "1:a"]
                
                sub_file = None
                sub_args = ["-vf", f"scale={width}:{height}"]
                
                if subtitles and subtitles.get("narrator"):
                    try:
                        sub_file = VideoComposer._generate_subtitle_file(subtitles, height, subtitle_settings)
                        if os.path.exists(sub_file):
                            file_size = os.path.getsize(sub_file)
                            log_file.write(f"[FFMPEG DEBUG] 字幕文件生成成功: {sub_file}, 大小: {file_size} 字节\n")
                            log_file.write(f"[FFMPEG DEBUG] 字幕缩放比例: {subtitle_scale}\n")
                            sub_args = ["-vf", f"scale={width}:{height},ass={sub_file}:subfontscale={subtitle_scale}"]
                        else:
                            log_file.write("[FFMPEG] 字幕文件不存在，跳过字幕\n")
                    except Exception as e:
                        log_file.write(f"[FFMPEG] 生成字幕文件失败: {e}\n")
                
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0", "-i", list_path,
                ] + audio_inputs + [
                    "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k",
                    "-t", str(image_duration)
                ]
                
                if filter_complex:
                    cmd += filter_complex
                cmd += map_args + sub_args + [output_path]
                
                log_file.write(f"[FFMPEG] 完整命令: {' '.join(cmd)}\n")
                log_file.write(f"[FFMPEG] list_path: {list_path}\n")
                log_file.write(f"[FFMPEG] audio_inputs: {audio_inputs}\n")
                log_file.write(f"[FFMPEG] filter_complex: {filter_complex}\n")
                log_file.write(f"[FFMPEG] map_args: {map_args}\n")
                log_file.write(f"[FFMPEG] sub_args: {sub_args}\n")
                log_file.write(f"[FFMPEG] output_path: {output_path}\n")
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                log_file.write(f"[FFMPEG] 返回码: {result.returncode}\n")
                log_file.write(f"[FFMPEG] 标准输出: {result.stdout}\n")
                log_file.write(f"[FFMPEG] 错误输出: {result.stderr}\n")
                
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    log_file.write(f"[FFMPEG DEBUG] 输出文件大小: {file_size} 字节\n")
                    if file_size < 1000:
                        log_file.write(f"[FFMPEG WARNING] 输出文件过小，可能合成失败\n")
                
                if sub_file and os.path.exists(sub_file):
                    os.remove(sub_file)
                
                if result.returncode != 0:
                    return False
                
                return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
            except FileNotFoundError:
                log_file.write("[FFMPEG] ffmpeg未安装\n")
                return False
            except Exception as e:
                log_file.write(f"[FFMPEG] 合成失败: {e}\n")
                import traceback
                log_file.write(f"[FFMPEG] 异常堆栈: {traceback.format_exc()}\n")
                return False
    
    @staticmethod
    def _get_audio_duration(audio_path: str) -> float:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True, text=True
            )
            return float(result.stdout.strip())
        except:
            return 60.0
    
    @staticmethod
    def _generate_subtitle_file(subtitles: dict, height: int = 1280, subtitle_settings: dict = None) -> str:
        sub_path = "output/subtitles.ass"
        
        if subtitle_settings is None:
            subtitle_settings = {
                "narrator_font_size": 50,
                "narrator_position": 25,
                "golden_font_size": 54,
                "golden_position": 35
            }
        
        narrator_font_size = subtitle_settings["narrator_font_size"]
        narrator_position = subtitle_settings["narrator_position"]
        golden_font_size = subtitle_settings["golden_font_size"]
        golden_position = subtitle_settings["golden_position"]
        
        narrator_margin_v = int(height * narrator_position / 100)
        golden_margin_v = int(height * golden_position / 100)
        
        with open(sub_path, 'w', encoding='utf-8') as f:
            f.write("[Script Info]\n")
            f.write("Title: Subtitles\n")
            f.write("ScriptType: v4.00+\n")
            f.write("WrapStyle: 2\n")
            f.write("ScaledBorderAndShadow: yes\n")
            f.write("\n")
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write(f"Style: Narrator,SimHei,{narrator_font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,2,2,10,10,{narrator_margin_v},1\n")
            f.write(f"Style: Golden,SimHei,{golden_font_size},&H00FFD700,&H00FFD700,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,{golden_margin_v},1\n")
            f.write("\n")
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            if subtitles.get("narrator"):
                for i, sub in enumerate(subtitles["narrator"], 1):
                    start_time = VideoComposer._format_time_ass(sub.get("start", i * 3))
                    end_time = VideoComposer._format_time_ass(sub.get("end", i * 3 + 3))
                    text = sub.get("text", "")[:40]
                    text = VideoComposer._wrap_text(text, 10)
                    text = text.replace("\n", "\\N")
                    f.write(f"Dialogue: 0,{start_time},{end_time},Narrator,,0,0,0,,{text}\n")
            
            if subtitles.get("golden"):
                golden_data = subtitles["golden"]
                if isinstance(golden_data, dict):
                    golden_texts = golden_data.get("text", [])
                    start_time = VideoComposer._format_time_ass(golden_data.get("start", 0))
                    end_time = VideoComposer._format_time_ass(golden_data.get("end", 10))
                else:
                    golden_texts = golden_data
                    start_time = VideoComposer._format_time_ass(0)
                    end_time = VideoComposer._format_time_ass(10)
                
                for text in golden_texts[:2]:
                    text = text[:40]
                    text = VideoComposer._wrap_text(text, 12)
                    text = text.replace("\n", "\\N")
                    f.write(f"Dialogue: 1,{start_time},{end_time},Golden,,0,0,0,,{text}\n")
        return sub_path
    
    @staticmethod
    def _wrap_text(text: str, max_chars_per_line: int = 10) -> str:
        lines = []
        current_line = ""
        for char in text:
            if len(current_line) >= max_chars_per_line:
                lines.append(current_line)
                current_line = char
                if len(lines) >= 2:
                    break
            else:
                current_line += char
        if current_line and len(lines) < 2:
            lines.append(current_line)
        return "\n".join(lines)
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")
    
    @staticmethod
    def _format_time_ass(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        ms = int((secs - int(secs)) * 100)
        return f"{hours:01d}:{minutes:02d}:{int(secs):02d}.{ms:02d}"
    
    @staticmethod
    def generate_cover(title: str, subtitle: str, first_image_path: str = "", width: int = 720, height: int = 1280) -> str:
        cover_path = "output/cover.png"
        
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
            
            if os.path.exists(first_image_path):
                canvas = Image.open(first_image_path)
            else:
                canvas = Image.new('RGB', (width, height), color=(50, 50, 50))
            
            canvas = canvas.resize((width, height))
            canvas = canvas.filter(ImageFilter.GaussianBlur(15))
            canvas = Image.blend(canvas, Image.new("RGB", (width, height), (0, 0, 0)), 0.35)
            
            draw = ImageDraw.Draw(canvas)
            
            title_font = None
            subtitle_font = None
            font_paths = ['simhei.ttf', 'simkai.ttf', 'simfang.ttf', 'simsun.ttc', 'arial.ttf']
            
            font_scale = min(width, height) / 1080
            title_font_size = int(72 * font_scale)
            subtitle_font_size = int(32 * font_scale)
            
            for font_path in font_paths:
                try:
                    title_font = ImageFont.truetype(font_path, title_font_size)
                    subtitle_font = ImageFont.truetype(font_path, subtitle_font_size)
                    break
                except:
                    continue
            if title_font is None:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
            
            title_text = title[:16]
            title_lines = []
            current_line = ""
            max_chars = max(6, width // (title_font_size * 2))
            for char in title_text:
                if len(current_line) >= max_chars:
                    if char in '，。！？、；：':
                        current_line += char
                        title_lines.append(current_line)
                        current_line = ""
                    else:
                        title_lines.append(current_line)
                        current_line = char
                else:
                    current_line += char
            if current_line:
                title_lines.append(current_line)
            title_lines = title_lines[:2]
            
            y = height // 3
            for line in title_lines:
                bbox = draw.textbbox((0, 0), line, font=title_font)
                text_width = bbox[2] - bbox[0]
                draw.text(((width - text_width) // 2, y), line, fill=(255, 215, 0), font=title_font)
                y += int(90 * font_scale)
            
            subtitle_text = subtitle[:18]
            bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = bbox[2] - bbox[0]
            draw.text(((width - subtitle_width) // 2, y + int(30 * font_scale)), subtitle_text, fill=(180, 180, 180), font=subtitle_font)
            
            canvas.save(cover_path)
            return cover_path
        except ImportError:
            print("[COVER] PIL未安装")
            return ""

class VideoMakerGUI:
    """可视化界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("家庭教育短视频制作工具 - MiniMax Token Plan版")
        self.root.geometry("1200x850")
        self.root.resizable(True, True)
        
        self.current_step = 0
        self.selected_topic = None
        self.generated_topics = []
        self.current_script = {}
        self.script_versions = []  # 保存所有脚本版本
        self.current_storyboard = []
        self.generated_images = []
        self.audio_path = ""
        self.bgm_path = ""
        self.current_subtitles = {}
        self.completed_steps = [0]
        
        self.ip_template = {
            "name": "",
            "track": "",
            "target_group": "",
            "pain_points": "",
            "gender": "女",  # IP性别，用于预设配音音色
            "age": "",       # IP年龄，用于角色描述
            "persona": "",   # 人设描述（如：温柔妈妈/专业导师）
            "tone": "专业温和",  # 语气风格
            "keywords": []   # 领域热门关键词
        }
        
        self.video_ratio_options = ["9:16", "3:4", "16:9"]
        self.video_resolution_options = {
            "9:16": [
                {"name": "标清", "width": 720, "height": 1280},
                {"name": "高清", "width": 1080, "height": 1920, "default": True},
                {"name": "超清", "width": 1440, "height": 2560}
            ],
            "3:4": [
                {"name": "标清", "width": 720, "height": 960},
                {"name": "高清", "width": 1080, "height": 1440, "default": True}
            ],
            "16:9": [
                {"name": "标清", "width": 1280, "height": 720},
                {"name": "高清", "width": 1920, "height": 1080, "default": True}
            ]
        }
        self.selected_ratio = "9:16"
        self.selected_resolution = self._get_default_resolution("9:16")
        
        for dir_name in ["output", "images", "audio", "subtitles"]:
            os.makedirs(dir_name, exist_ok=True)
        
        self._load_config()
        
        self.minimax = MiniMaxConnector(API_CONFIG)
        self.qwen_image = QwenImageConnector(API_CONFIG)
        
        self._setup_styles()
        self._create_menu()
        self.create_widgets()
        
        self._try_load_project()  # 启动时尝试加载之前保存的项目
    
    def _setup_styles(self):
        style = ttk.Style()
        style.configure('CurrentStep.TButton', 
                       background='#1E90FF', 
                       foreground='white',
                       font=('Arial', 10, 'bold'))
        style.map('CurrentStep.TButton',
                  background=[('active', '#1874CD')])
        
        style.configure('CompletedStep.TButton', 
                       background='#98FB98', 
                       foreground='#333333',
                       font=('Arial', 10))
        style.map('CompletedStep.TButton',
                  background=[('active', '#90EE90')])
        
        style.configure('DisabledStep.TButton', 
                       background='#F5F5F5', 
                       foreground='#999999',
                       font=('Arial', 10))
    
    def _get_default_resolution(self, ratio):
        for res in self.video_resolution_options.get(ratio, []):
            if res.get("default"):
                return res
        return self.video_resolution_options.get(ratio, [{}])[0]
    
    def _get_subtitle_scale(self):
        base_height = 1080
        current_height = self.selected_resolution.get("height", 1080)
        return min(1.0, base_height / current_height)
    
    def _update_resolution_options(self):
        resolutions = self.video_resolution_options.get(self.selected_ratio, [])
        resolution_names = [res["name"] for res in resolutions]
        self.resolution_combobox["values"] = resolution_names
        if resolution_names:
            self.resolution_combobox.set(self.selected_resolution.get("name", resolution_names[0]))
    
    def _on_ratio_changed(self, event):
        self.selected_ratio = self.ratio_combobox.get()
        self.selected_resolution = self._get_default_resolution(self.selected_ratio)
        self._update_resolution_options()
        
        self.subtitle_settings = self.ratio_subtitle_defaults.get(self.selected_ratio, self.ratio_subtitle_defaults["9:16"])
        self.log(f"视频比例已更改为: {self.selected_ratio}")
        self.log(f"字幕设置已更新为{self.selected_ratio}默认值")
    
    def _on_resolution_changed(self, event):
        resolution_name = self.resolution_combobox.get()
        resolutions = self.video_resolution_options.get(self.selected_ratio, [])
        for res in resolutions:
            if res["name"] == resolution_name:
                self.selected_resolution = res
                break
        width = self.selected_resolution.get("width", 720)
        height = self.selected_resolution.get("height", 1280)
        self.log(f"分辨率已更改为: {width}x{height}")
    
    def _show_subtitle_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("字幕样式设置")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        settings = self.subtitle_settings.copy()
        
        ttk.Label(dialog, text="旁白字幕设置", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(dialog, text="字号 (20-80pt):").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        narrator_font_var = tk.IntVar(value=settings["narrator_font_size"])
        narrator_font_spin = ttk.Spinbox(dialog, from_=20, to=80, textvariable=narrator_font_var, width=10)
        narrator_font_spin.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="底边距 (5-40%):").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        narrator_pos_var = tk.IntVar(value=settings["narrator_position"])
        narrator_pos_spin = ttk.Spinbox(dialog, from_=5, to=40, textvariable=narrator_pos_var, width=10)
        narrator_pos_spin.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="金句字幕设置", font=('Arial', 12, 'bold')).grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Label(dialog, text="字号 (24-84pt):").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        golden_font_var = tk.IntVar(value=settings["golden_font_size"])
        golden_font_spin = ttk.Spinbox(dialog, from_=24, to=84, textvariable=golden_font_var, width=10)
        golden_font_spin.grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="底边距 (15-50%):").grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        golden_pos_var = tk.IntVar(value=settings["golden_position"])
        golden_pos_spin = ttk.Spinbox(dialog, from_=15, to=50, textvariable=golden_pos_var, width=10)
        golden_pos_spin.grid(row=5, column=1, padx=10, pady=5)
        
        def apply_settings():
            narrator_font = narrator_font_var.get()
            narrator_pos = narrator_pos_var.get()
            golden_font = golden_font_var.get()
            golden_pos = golden_pos_var.get()
            
            if golden_pos <= narrator_pos:
                tk.messagebox.showwarning("警告", "金句位置必须在旁白位置之上！")
                return
            
            self.subtitle_settings = {
                "narrator_font_size": narrator_font,
                "narrator_position": narrator_pos,
                "golden_font_size": golden_font,
                "golden_position": golden_pos
            }
            self.log(f"字幕设置已更新: 旁白{self.subtitle_settings['narrator_font_size']}pt/{self.subtitle_settings['narrator_position']}%, 金句{self.subtitle_settings['golden_font_size']}pt/{self.subtitle_settings['golden_position']}%")
            dialog.destroy()
        
        def reset_settings():
            narrator_font_var.set(50)
            narrator_pos_var.set(25)
            golden_font_var.set(54)
            golden_pos_var.set(35)
        
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="应用", command=apply_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="重置", command=reset_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
        dialog.wait_window()
    
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建项目", command=self.new_project)
        file_menu.add_command(label="保存项目", command=self.save_project)
        file_menu.add_command(label="加载项目", command=self.load_project)
        file_menu.add_command(label="删除项目", command=self.delete_project)
        file_menu.add_separator()
        file_menu.add_command(label="IP模板设置", command=self.open_ip_template)
        file_menu.add_command(label="API配置", command=self.open_api_config)
        file_menu.add_command(label="存储位置设置", command=self.open_storage_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="菜单", menu=file_menu)
        
        self.root.config(menu=menubar)
    
    def _load_config(self):
        if os.path.exists("api_config.json"):
            try:
                with open("api_config.json", 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    API_CONFIG.update(saved_config)
            except:
                pass
    
    def _save_config(self):
        with open("api_config.json", 'w', encoding='utf-8') as f:
            json.dump(API_CONFIG, f, ensure_ascii=False, indent=2)
    
    def new_project(self):
        """新建项目，重置所有状态"""
        if messagebox.askyesno("确认新建", "确定要新建项目吗？\n当前项目进度将丢失！"):
            self.current_step = 0
            self.selected_topic = None
            self.generated_topics = []
            self.current_script = {}
            self.current_storyboard = []
            self.generated_images = []
            self.audio_path = ""
            self.bgm_path = ""
            self.current_subtitles = {}
            self.completed_steps = [0]
            
            self.update_ui()
            
            if hasattr(self, 'topic_listbox'):
                self.topic_listbox.delete(0, tk.END)
            if hasattr(self, 'script_text'):
                self.script_text.delete(1.0, tk.END)
            
            self.log("已新建项目")
            messagebox.showinfo("新建成功", "项目已重置，可以开始新的制作")
    
    def save_project(self):
        """保存当前项目进度"""
        project_data = {
            "current_step": self.current_step,
            "selected_topic": self.selected_topic,
            "generated_topics": self.generated_topics,
            "current_script": self.current_script,
            "script_versions": self.script_versions,  # 保存所有脚本版本
            "current_storyboard": self.current_storyboard,
            "generated_images": self.generated_images,
            "audio_path": self.audio_path,
            "bgm_path": self.bgm_path,
            "current_subtitles": self.current_subtitles,
            "completed_steps": self.completed_steps,
            "selected_ratio": self.selected_ratio,
            "selected_resolution": self.selected_resolution,
            "subtitle_settings": self.subtitle_settings,
            "script_word_count": self.script_word_count,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("current_project.json", 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        self.log("项目已保存")
        messagebox.showinfo("保存成功", "项目进度已保存到 current_project.json")
    
    def load_project(self):
        """加载之前保存的项目"""
        if not os.path.exists("current_project.json"):
            messagebox.showwarning("警告", "没有找到保存的项目文件")
            return
        
        try:
            with open("current_project.json", 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            self.current_step = project_data.get("current_step", 0)
            self.selected_topic = project_data.get("selected_topic")
            self.generated_topics = project_data.get("generated_topics", [])
            self.current_script = project_data.get("current_script", {})
            self.script_versions = project_data.get("script_versions", [])  # 加载脚本版本
            self.current_storyboard = project_data.get("current_storyboard", [])
            self.generated_images = project_data.get("generated_images", [])
            self.audio_path = project_data.get("audio_path", "")
            self.bgm_path = project_data.get("bgm_path", "")
            self.current_subtitles = project_data.get("current_subtitles", {})
            self.completed_steps = project_data.get("completed_steps", [0])
            self.selected_ratio = project_data.get("selected_ratio", "9:16")
            self.selected_resolution = project_data.get("selected_resolution", self._get_default_resolution("9:16"))
            self.subtitle_settings = project_data.get("subtitle_settings", {
                "narrator_font_size": 50,
                "narrator_position": 25,
                "golden_font_size": 54,
                "golden_position": 35
            })
            self.script_word_count = project_data.get("script_word_count", {
                "min_words": 250,
                "max_words": 300
            })
            
            self.log(f"已加载项目，当前步骤: {self.current_step + 1}")
            self.log(f"视频设置: {self.selected_ratio} {self.selected_resolution.get('width', 0)}x{self.selected_resolution.get('height', 0)}")
            
            # 更新UI
            self.update_ui()
            
            # 更新选题列表
            if self.current_step >= 0 and self.generated_topics:
                self.topic_listbox.delete(0, tk.END)
                for topic in self.generated_topics:
                    if isinstance(topic, dict) and 'title' in topic and 'score' in topic and 'reason' in topic:
                        display_text = f"【推荐分 {topic['score']}】{topic['title']} - {topic['reason']}"
                        self.topic_listbox.insert(tk.END, display_text)
            
            # 更新脚本显示
            if self.current_step >= 1 and self.current_script:
                self.script_text.delete(1.0, tk.END)
                self.script_text.insert(tk.END, "【开场钩子】\n")
                self.script_text.insert(tk.END, self.current_script.get("opening", "") + "\n\n")
                self.script_text.insert(tk.END, "【核心干货】\n")
                self.script_text.insert(tk.END, self.current_script.get("content", "") + "\n\n")
                self.script_text.insert(tk.END, "【CTA引导】\n")
                self.script_text.insert(tk.END, self.current_script.get("cta", ""))
            
            messagebox.showinfo("加载成功", f"项目已加载，当前步骤: {self.current_step + 1}/6")
        except Exception as e:
            self.log(f"加载项目失败: {e}")
            messagebox.showerror("错误", f"加载项目失败: {e}")
    
    def delete_project(self):
        """删除当前项目（包括相关文件）"""
        if not os.path.exists("current_project.json"):
            messagebox.showwarning("警告", "没有找到保存的项目文件")
            return
        
        if not messagebox.askyesno("确认删除", "确定要删除当前项目吗？\n这将删除所有生成的图片、音频和视频文件！"):
            return
        
        try:
            # 删除项目文件
            os.remove("current_project.json")
            
            # 删除图片文件
            for img_path in self.generated_images:
                if os.path.exists(img_path):
                    os.remove(img_path)
            
            # 删除音频文件
            audio_files = ["audio/voice.mp3", "audio/voiceover.mp3", "audio/bgm.mp3"]
            for audio_file in audio_files:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            
            # 删除视频文件
            video_files = ["output/final_with_audio.mp4", "output/cover.png", "output/delivery清单.json", "output/images.txt"]
            for video_file in video_files:
                if os.path.exists(video_file):
                    os.remove(video_file)
            
            # 重置状态
            self.current_step = 0
            self.selected_topic = None
            self.generated_topics = []
            self.current_script = {}
            self.current_storyboard = []
            self.generated_images = []
            self.audio_path = ""
            self.bgm_path = ""
            self.current_subtitles = {}
            self.completed_steps = [0]
            
            self.update_ui()
            self.topic_listbox.delete(0, tk.END)
            self.script_text.delete(1.0, tk.END)
            
            self.log("项目已删除")
            messagebox.showinfo("删除成功", "项目已删除，所有相关文件已清理")
        except Exception as e:
            self.log(f"删除项目失败: {e}")
            messagebox.showerror("错误", f"删除项目失败: {e}")
    
    def _auto_save(self):
        """自动保存项目（在每个步骤完成后调用）"""
        if self.current_script or self.current_storyboard or self.generated_images:
            self.save_project()
    
    def _try_load_project(self):
        """启动时尝试自动加载之前保存的项目"""
        if os.path.exists("current_project.json"):
            try:
                with open("current_project.json", 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                saved_at = project_data.get("saved_at", "")
                if messagebox.askyesno("加载项目", f"检测到之前保存的项目（{saved_at}），是否加载？"):
                    self.load_project()
            except:
                pass
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.step_label = ttk.Label(title_frame, text="步骤 1/7：生成选题", font=('Arial', 14, 'bold'))
        self.step_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(title_frame, length=300, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=20)
        self.progress_bar['value'] = 0
        
        left_frame = ttk.Frame(main_frame, width=150)
        left_frame.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.N, tk.S))
        left_frame.columnconfigure(0, weight=1)
        
        video_settings_frame = ttk.LabelFrame(left_frame, text="视频设置", padding="10")
        video_settings_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(video_settings_frame, text="高宽比:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ratio_combobox = ttk.Combobox(video_settings_frame, values=self.video_ratio_options, state="readonly", width=10)
        self.ratio_combobox.set(self.selected_ratio)
        self.ratio_combobox.grid(row=0, column=1, padx=5, pady=3)
        self.ratio_combobox.bind("<<ComboboxSelected>>", self._on_ratio_changed)
        
        ttk.Label(video_settings_frame, text="分辨率:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.resolution_combobox = ttk.Combobox(video_settings_frame, state="readonly", width=10)
        self.resolution_combobox.grid(row=1, column=1, padx=5, pady=3)
        self._update_resolution_options()
        self.resolution_combobox.bind("<<ComboboxSelected>>", self._on_resolution_changed)
        
        subtitle_settings_frame = ttk.LabelFrame(left_frame, text="字幕设置", padding="10")
        subtitle_settings_frame.grid(row=2, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.subtitle_settings_btn = ttk.Button(subtitle_settings_frame, text="设置字幕样式", 
                                               command=self._show_subtitle_settings, width=12)
        self.subtitle_settings_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        self.subtitle_settings = {
            "narrator_font_size": 50,
            "narrator_position": 25,
            "golden_font_size": 54,
            "golden_position": 35
        }
        
        self.script_word_count = {
            "min_words": 250,
            "max_words": 300
        }
        
        self.ratio_subtitle_defaults = {
            "9:16": {"narrator_font_size": 50, "narrator_position": 25, "golden_font_size": 54, "golden_position": 35},
            "3:4": {"narrator_font_size": 48, "narrator_position": 22, "golden_font_size": 52, "golden_position": 32},
            "16:9": {"narrator_font_size": 36, "narrator_position": 12, "golden_font_size": 40, "golden_position": 20}
        }
        
        config_frame = ttk.LabelFrame(left_frame, text="步骤导航", padding="10")
        config_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.N, tk.S))
        config_frame.rowconfigure(10, weight=1)
        
        self.step_buttons = []
        steps = ["选题生成", "脚本创作", "分镜设计", "图片生成", "音频制作", "视频合成"]
        for i, step in enumerate(steps):
            btn = ttk.Button(config_frame, text=step, command=lambda idx=i: self.go_to_step(idx), 
                            state=tk.NORMAL if i == 0 else tk.DISABLED, width=12)
            btn.grid(row=i+1, column=0, sticky=(tk.W, tk.E), pady=2)
            self.step_buttons.append(btn)
        
        # 创建内容区域（带滚动条）
        content_frame_container = ttk.Frame(main_frame)
        content_frame_container.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 垂直滚动条
        self.content_scrollbar_y = ttk.Scrollbar(content_frame_container, orient=tk.VERTICAL)
        self.content_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        self.content_scrollbar_x = ttk.Scrollbar(content_frame_container, orient=tk.HORIZONTAL)
        self.content_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 内容区域
        self.content_frame = ttk.LabelFrame(content_frame_container, text="内容区域", padding="10")
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定滚动条
        self.content_canvas = tk.Canvas(self.content_frame, 
                                        yscrollcommand=self.content_scrollbar_y.set,
                                        xscrollcommand=self.content_scrollbar_x.set)
        self.content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.content_scrollbar_y.config(command=self.content_canvas.yview)
        self.content_scrollbar_x.config(command=self.content_canvas.xview)
        
        # 实际内容框架
        self.inner_content_frame = ttk.Frame(self.content_canvas)
        self.inner_content_frame.bind("<Configure>", lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))
        self.content_canvas.create_window((0, 0), window=self.inner_content_frame, anchor="nw")
        
        # 使用inner_content_frame作为内容容器
        self.content_frame = self.inner_content_frame
        
        self.topic_listbox = tk.Listbox(self.content_frame, width=80, height=15)
        self.topic_listbox.grid(row=0, column=0, padx=10, pady=10)
        
        self.script_text = scrolledtext.ScrolledText(self.content_frame, width=80, height=15)
        
        action_frame = ttk.LabelFrame(main_frame, text="操作", padding="10")
        action_frame.grid(row=1, column=2, padx=10, pady=10, sticky=(tk.N, tk.S))
        
        self.generate_btn = ttk.Button(action_frame, text="生成", command=self.generate_current_step)
        self.generate_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.confirm_btn = ttk.Button(action_frame, text="确认", command=self.confirm_current_step, state=tk.DISABLED)
        self.confirm_btn.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.regenerate_btn = ttk.Button(action_frame, text="重新生成", command=self.regenerate_current_step, state=tk.DISABLED)
        self.regenerate_btn.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.preview_btn = ttk.Button(action_frame, text="预览", command=self.preview_result, state=tk.DISABLED)
        self.preview_btn.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky=(tk.W, tk.E))
        main_frame.rowconfigure(2, weight=0)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        log_frame.columnconfigure(0, weight=1)
        
        self._update_config_status()
    
    def _update_config_status(self):
        minimax_configured = bool(API_CONFIG["minimax"]["api_key"])
        qwen_configured = bool(API_CONFIG["qwen_image"]["api_key"])
        
        if minimax_configured:
            self.log("MiniMax Token Plan API 已配置")
        if qwen_configured:
            self.log("Qwen Image API 已配置")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def _load_ip_templates(self):
        """加载IP档案"""
        import json
        import os
        
        templates_file = "ip_templates.json"
        if os.path.exists(templates_file):
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("templates", [])
            except:
                return []
        return []
    
    def _save_ip_templates(self, templates):
        """保存IP档案"""
        import json
        import os
        
        templates_file = "ip_templates.json"
        try:
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump({"templates": templates}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] 保存IP档案失败: {e}")
            return False
    
    def open_ip_template(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("IP模板设置")
        config_window.geometry("850x500")
        
        # 设置为模态窗口，始终在主窗口上方
        config_window.transient(self.root)
        config_window.grab_set()
        
        # 居中显示
        config_window.update_idletasks()
        x = (config_window.winfo_screenwidth() // 2) - (850 // 2)
        y = (config_window.winfo_screenheight() // 2) - (500 // 2)
        config_window.geometry(f"850x500+{x}+{y}")
        
        # 人设预设选项
        PERSONA_OPTIONS = ["温柔妈妈", "专业教育导师", "幽默奶爸", "知心姐姐", "严师益友", "亲子陪伴者", "智慧家长", "其他"]
        # 热门关键词建议
        HOT_KEYWORDS = ["家庭教育", "亲子沟通", "学习方法", "情绪管理", "亲子关系", "专注力", "习惯养成", "思维训练", "时间管理", "自信心"]
        
        # 左半部分：IP档案列表
        left_frame = ttk.LabelFrame(config_window, text="📁 IP档案库", width=280)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
        left_frame.grid_propagate(False)
        
        # 档案列表（带滚动条）
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.template_listbox = tk.Listbox(listbox_frame, width=35, height=18, yscrollcommand=scrollbar.set, selectbackground="#4a90d9", selectforeground="white")
        scrollbar.config(command=self.template_listbox.yview)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.template_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 加载档案
        self.ip_templates = self._load_ip_templates()
        for template in self.ip_templates:
            self.template_listbox.insert(tk.END, template.get("name", "未命名"))
        
        # 档案操作按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=1, column=0, pady=10)
        
        def load_template():
            selected_idx = self.template_listbox.curselection()
            if selected_idx:
                idx = selected_idx[0]
                template = self.ip_templates[idx]
                
                # 加载基本信息
                ip_name.delete(0, tk.END)
                ip_name.insert(0, template.get("name", ""))
                track.delete(0, tk.END)
                track.insert(0, template.get("track", ""))
                target_group.delete(0, tk.END)
                target_group.insert(0, template.get("target_group", ""))
                pain_points.delete(0, tk.END)
                pain_points.insert(0, template.get("pain_points", ""))
                gender_combo.set(template.get("gender", "女"))
                
                # 加载年龄
                age_entry.delete(0, tk.END)
                age_entry.insert(0, template.get("age", ""))
                
                # 加载人设描述（处理不在预设选项中的情况）
                persona_value = template.get("persona", "")
                if persona_value in PERSONA_OPTIONS:
                    persona_combo.set(persona_value)
                    persona_custom.delete(0, tk.END)
                else:
                    persona_combo.set("其他")
                    persona_custom.delete(0, tk.END)
                    persona_custom.insert(0, persona_value)
                
                # 加载语气风格
                tone_combo.set(template.get("tone", "专业温和"))
                
                # 加载关键词
                keywords_entry.delete(0, tk.END)
                keywords_entry.insert(0, ", ".join(template.get("keywords", [])))
                
                messagebox.showinfo("✅ 加载成功", f"已加载IP: {template.get('name', '未命名')}", parent=config_window)
        
        def save_to_archive():
            if not ip_name.get().strip():
                messagebox.showwarning("⚠️ 警告", "请先输入IP名称", parent=config_window)
                return
            
            # 获取人设（如果自定义输入框有值，优先使用自定义输入）
            persona_value = persona_custom.get().strip() if persona_custom.get().strip() else persona_combo.get()
            
            # 解析关键词（逗号分隔）
            keywords_list = [k.strip() for k in keywords_entry.get().split(",") if k.strip()]
            
            new_template = {
                "name": ip_name.get().strip(),
                "track": track.get().strip(),
                "target_group": target_group.get().strip(),
                "pain_points": pain_points.get().strip(),
                "gender": gender_combo.get(),
                "age": age_entry.get().strip(),
                "persona": persona_value,
                "tone": tone_combo.get(),
                "keywords": keywords_list
            }
            
            # 检查是否已存在同名IP
            exists = False
            update_idx = -1
            for i, template in enumerate(self.ip_templates):
                if template["name"] == new_template["name"]:
                    update_idx = i
                    exists = True
                    break
            
            if exists:
                if messagebox.askyesno("🔄 更新确认", f"IP档案 '{new_template['name']}' 已存在，确定要更新吗？", parent=config_window):
                    self.ip_templates[update_idx] = new_template
                else:
                    return
            else:
                self.ip_templates.append(new_template)
            
            if self._save_ip_templates(self.ip_templates):
                # 更新列表
                self.template_listbox.delete(0, tk.END)
                for template in self.ip_templates:
                    self.template_listbox.insert(tk.END, template.get("name", "未命名"))
                messagebox.showinfo("✅ 保存成功", f"IP档案已{'更新' if exists else '保存'}: {new_template['name']}", parent=config_window)
            else:
                messagebox.showerror("❌ 保存失败", "保存IP档案时发生错误", parent=config_window)
        
        def delete_template():
            selected_idx = self.template_listbox.curselection()
            if selected_idx:
                idx = selected_idx[0]
                template_name = self.ip_templates[idx].get("name", "未命名")
                if messagebox.askyesno("🗑️ 确认删除", f"确定要删除IP档案 '{template_name}' 吗？此操作无法撤销。", parent=config_window):
                    del self.ip_templates[idx]
                    if self._save_ip_templates(self.ip_templates):
                        self.template_listbox.delete(idx)
                        messagebox.showinfo("✅ 删除成功", f"已删除IP档案: {template_name}", parent=config_window)
        
        ttk.Button(btn_frame, text="📥 加载", command=load_template, width=10).grid(row=0, column=0, padx=3)
        ttk.Button(btn_frame, text="💾 保存/更新", command=save_to_archive, width=12).grid(row=0, column=1, padx=3)
        ttk.Button(btn_frame, text="🗑️ 删除", command=delete_template, width=10).grid(row=0, column=2, padx=3)
        
        # 右半部分：当前IP模板编辑
        right_frame = ttk.LabelFrame(config_window, text="✏️ 当前IP模板")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # 表单网格布局
        row = 0
        
        # 名称
        ttk.Label(right_frame, text="名称 *", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=8, padx=10)
        ip_name = ttk.Entry(right_frame, width=45, font=('Arial', 10))
        ip_name.insert(0, self.ip_template.get("name", ""))
        ip_name.grid(row=row, column=1, padx=10)
        row += 1
        
        # 赛道
        ttk.Label(right_frame, text="赛道", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=8, padx=10)
        track = ttk.Entry(right_frame, width=45, font=('Arial', 10))
        track.insert(0, self.ip_template.get("track", ""))
        track.grid(row=row, column=1, padx=10)
        row += 1
        
        # 目标群体
        ttk.Label(right_frame, text="目标群体", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=8, padx=10)
        target_group = ttk.Entry(right_frame, width=45, font=('Arial', 10))
        target_group.insert(0, self.ip_template.get("target_group", ""))
        target_group.grid(row=row, column=1, padx=10)
        row += 1
        
        # 目标群体痛点
        ttk.Label(right_frame, text="目标群体痛点", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=8, padx=10)
        pain_points = ttk.Entry(right_frame, width=45, font=('Arial', 10))
        pain_points.insert(0, self.ip_template.get("pain_points", ""))
        pain_points.grid(row=row, column=1, padx=10)
        row += 1
        
        # IP性别
        ttk.Label(right_frame, text="IP性别", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=8, padx=10)
        gender_combo = ttk.Combobox(right_frame, values=["女", "男", "中性"], width=12, font=('Arial', 10), state="readonly")
        gender_combo.set(self.ip_template.get("gender", "女"))
        gender_combo.grid(row=row, column=1, padx=10, sticky=tk.W)
        row += 1
        
        # IP年龄
        ttk.Label(right_frame, text="IP年龄", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=8, padx=10)
        age_entry = ttk.Entry(right_frame, width=10, font=('Arial', 10))
        age_entry.insert(0, self.ip_template.get("age", ""))
        age_entry.grid(row=row, column=1, padx=10, sticky=tk.W)
        row += 1
        
        # 人设描述（预设选项+自定义）
        ttk.Label(right_frame, text="人设描述", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=8, padx=10)
        persona_frame = ttk.Frame(right_frame)
        persona_frame.grid(row=row, column=1, sticky=tk.W)
        persona_combo = ttk.Combobox(persona_frame, values=PERSONA_OPTIONS, width=18, font=('Arial', 10), state="readonly")
        persona_combo.set(self.ip_template.get("persona", "") if self.ip_template.get("persona", "") in PERSONA_OPTIONS else "其他")
        persona_combo.pack(side=tk.LEFT)
        persona_custom = ttk.Entry(persona_frame, width=25, font=('Arial', 10))
        if self.ip_template.get("persona", "") and self.ip_template.get("persona") not in PERSONA_OPTIONS:
            persona_custom.insert(0, self.ip_template.get("persona", ""))
        persona_custom.pack(side=tk.LEFT, padx=5)
        row += 1
        
        # 语气风格
        ttk.Label(right_frame, text="语气风格", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=8, padx=10)
        tone_combo = ttk.Combobox(right_frame, values=["专业温和", "温柔亲切", "专业权威", "幽默风趣", "温暖治愈", "睿智沉稳"], width=15, font=('Arial', 10), state="readonly")
        tone_combo.set(self.ip_template.get("tone", "专业温和"))
        tone_combo.grid(row=row, column=1, padx=10, sticky=tk.W)
        row += 1
        
        # 关键词（带热门关键词提示）
        ttk.Label(right_frame, text="领域热门关键词", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=8, padx=10)
        keywords_entry = ttk.Entry(right_frame, width=45, font=('Arial', 10))
        keywords_entry.insert(0, ", ".join(self.ip_template.get("keywords", [])))
        keywords_entry.grid(row=row, column=1, padx=10)
        row += 1
        
        # 热门关键词快速选择
        keywords_tip_frame = ttk.LabelFrame(right_frame, text="热门关键词（点击添加）")
        keywords_tip_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        def add_keyword(keyword):
            current = keywords_entry.get().strip()
            if current:
                if keyword not in current:
                    keywords_entry.delete(0, tk.END)
                    keywords_entry.insert(0, current + ", " + keyword)
            else:
                keywords_entry.insert(0, keyword)
        
        kw_row, kw_col = 0, 0
        for kw in HOT_KEYWORDS:
            ttk.Button(keywords_tip_frame, text=kw, command=lambda k=kw: add_keyword(k), width=12).grid(row=kw_row, column=kw_col, padx=3, pady=3)
            kw_col += 1
            if kw_col >= 5:
                kw_row += 1
                kw_col = 0
        
        ttk.Label(right_frame, text="💡 提示：多个关键词用英文逗号分隔，如：家庭教育, 亲子沟通", font=('Arial', 8), foreground='gray').grid(row=row+1, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        row += 2
        
        # 应用按钮
        def save_current_template():
            persona_value = persona_custom.get().strip() if persona_combo.get() == "其他" else persona_combo.get()
            
            self.ip_template["name"] = ip_name.get()
            self.ip_template["track"] = track.get()
            self.ip_template["target_group"] = target_group.get()
            self.ip_template["pain_points"] = pain_points.get()
            self.ip_template["gender"] = gender_combo.get()
            self.ip_template["age"] = age_entry.get().strip()
            self.ip_template["persona"] = persona_value
            self.ip_template["tone"] = tone_combo.get()
            self.ip_template["keywords"] = [k.strip() for k in keywords_entry.get().split(",") if k.strip()]
            messagebox.showinfo("✅ 应用成功", "当前IP模板已保存并应用到项目", parent=config_window)
        
        apply_btn = ttk.Button(right_frame, text="🚀 应用到当前项目", command=save_current_template, width=20)
        apply_btn.grid(row=row, column=0, columnspan=2, pady=15)
        
        # 窗口大小调整
        config_window.grid_columnconfigure(1, weight=1)
        config_window.grid_rowconfigure(0, weight=1)
    
    def open_storage_config(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("存储位置设置")
        config_window.geometry("400x200")
        
        ttk.Label(config_window, text="当前存储位置:").grid(row=0, column=0, sticky=tk.W, pady=10)
        ttk.Label(config_window, text="output/ - 视频输出").grid(row=1, column=0, sticky=tk.W, padx=20)
        ttk.Label(config_window, text="images/ - 生成图片").grid(row=2, column=0, sticky=tk.W, padx=20)
        ttk.Label(config_window, text="audio/ - 音频文件").grid(row=3, column=0, sticky=tk.W, padx=20)
        ttk.Label(config_window, text="subtitles/ - 字幕文件").grid(row=4, column=0, sticky=tk.W, padx=20)
        
        def open_output_folder():
            import os
            os.startfile("output")
        
        ttk.Button(config_window, text="打开输出文件夹", command=open_output_folder).grid(row=5, column=0, pady=10)
    
    def open_api_config(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("API配置 - MiniMax Token Plan")
        config_window.geometry("500x450")
        
        ttk.Label(config_window, text="=== MiniMax Token Plan 配置 ===").grid(row=0, column=0, sticky=tk.W, pady=10)
        
        ttk.Label(config_window, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        minimax_key = ttk.Entry(config_window, width=50)
        minimax_key.insert(0, API_CONFIG["minimax"]["api_key"])
        minimax_key.grid(row=1, column=1, padx=10)
        
        ttk.Label(config_window, text="文本模型:").grid(row=2, column=0, sticky=tk.W)
        text_model_combo = ttk.Combobox(config_window, values=["MiniMax-M2.7", "MiniMax-M2.5", "MiniMax-M2.1"], width=45)
        text_model_combo.set(API_CONFIG["minimax"]["text_model"])
        text_model_combo.grid(row=2, column=1, padx=10)
        
        ttk.Label(config_window, text="语音模型:").grid(row=3, column=0, sticky=tk.W)
        speech_model_combo = ttk.Combobox(config_window, values=["speech-2.8-hd", "speech-2.6-hd", "speech-02-hd"], width=45)
        speech_model_combo.set(API_CONFIG["minimax"]["speech_model"])
        speech_model_combo.grid(row=3, column=1, padx=10)
        
        ttk.Label(config_window, text="音乐模型:").grid(row=4, column=0, sticky=tk.W)
        music_model_combo = ttk.Combobox(config_window, values=["Music-2.0"], width=45)
        music_model_combo.set(API_CONFIG["minimax"]["music_model"])
        music_model_combo.grid(row=4, column=1, padx=10)
        
        ttk.Label(config_window, text="=== Qwen Image 2.0 配置 ===").grid(row=5, column=0, sticky=tk.W, pady=10)
        
        ttk.Label(config_window, text="API Key:").grid(row=6, column=0, sticky=tk.W)
        qwen_key = ttk.Entry(config_window, width=50)
        qwen_key.insert(0, API_CONFIG["qwen_image"]["api_key"])
        qwen_key.grid(row=6, column=1, padx=10)
        
        def save_config():
            API_CONFIG["minimax"]["api_key"] = minimax_key.get()
            API_CONFIG["minimax"]["text_model"] = text_model_combo.get()
            API_CONFIG["minimax"]["speech_model"] = speech_model_combo.get()
            API_CONFIG["minimax"]["music_model"] = music_model_combo.get()
            API_CONFIG["qwen_image"]["api_key"] = qwen_key.get()
            
            self._save_config()
            self._update_config_status()
            
            self.minimax = MiniMaxConnector(API_CONFIG)
            self.qwen_image = QwenImageConnector(API_CONFIG)
            
            messagebox.showinfo("保存成功", "API配置已保存")
            config_window.destroy()
        
        ttk.Button(config_window, text="保存配置", command=save_config).grid(row=7, column=0, columnspan=2, pady=10)
        
        info_text = """
=== MiniMax Token Plan 49元档说明 ===
支持模型：
  • 文本：MiniMax-M2.7（5小时滚动窗口）
  • 语音：TTS HD（speech-2.8-hd等，每日配额）
  • 音乐：Music-2.6（最长5分钟，每日配额）
  • 图像：image-01（每日配额）
  
获取API Key：
1. 登录 https://platform.minimaxi.com
2. 进入「接口密钥」
3. 创建「Token Plan Key」

注意事项：
• Token Plan Key 专用于订阅套餐
• 不同模型有独立的每日配额
• 达到限额可升级套餐或切换到按量付费
        """
        ttk.Label(config_window, text=info_text, justify=tk.LEFT).grid(row=8, column=0, columnspan=2, pady=10)
    
    def go_to_step(self, step):
        if step in self.completed_steps:
            self.current_step = step
            self.update_ui()
            self.log(f"跳转到步骤 {step+1}")
    
    def update_ui(self):
        steps = ["选题生成", "脚本创作", "分镜设计", "图片生成", "音频制作", "视频合成"]
        self.step_label.config(text=f"步骤 {self.current_step+1}/6：{steps[self.current_step]}")
        self.progress_bar['value'] = (self.current_step + 1) * 16.67
        
        for i, btn in enumerate(self.step_buttons):
            if i == self.current_step:
                btn.config(state=tk.NORMAL, style='CurrentStep.TButton')
            elif i in self.completed_steps:
                btn.config(state=tk.NORMAL, style='CompletedStep.TButton')
            else:
                btn.config(state=tk.DISABLED, style='DisabledStep.TButton')
        
        self.generate_btn.config(state=tk.NORMAL)
        
        if self.current_step == 0 and len(self.generated_topics) > 0:
            self.generate_btn.config(state=tk.DISABLED)
        elif self.current_step == 1 and self.current_script:
            self.generate_btn.config(state=tk.DISABLED)
        elif self.current_step == 2 and self.current_storyboard:
            self.generate_btn.config(state=tk.DISABLED)
        elif self.current_step == 3 and self.generated_images:
            self.generate_btn.config(state=tk.DISABLED)
        elif self.current_step == 4 and (self.audio_path or self.bgm_path):
            self.generate_btn.config(state=tk.DISABLED)
        elif self.current_step == 5:
            if not self.generated_images:
                self.generate_btn.config(state=tk.DISABLED)
            elif not self.audio_path:
                self.generate_btn.config(state=tk.DISABLED)
            else:
                if os.path.exists("output/final_with_audio.mp4"):
                    self.generate_btn.config(text="重新生成", state=tk.NORMAL)
                else:
                    self.generate_btn.config(text="生成视频", state=tk.NORMAL)
        
        for widget in self.content_frame.winfo_children():
            widget.grid_remove()
        
        if self.current_step == 0:
            self.topic_listbox.grid(row=0, column=0, padx=10, pady=10)
        elif self.current_step == 1:
            # 版本选择区域
            version_frame = ttk.Frame(self.content_frame)
            version_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky=(tk.W, tk.E))
            
            ttk.Label(version_frame, text="脚本版本:").grid(row=0, column=0, padx=5)
            
            # 每次都创建新的版本列表（绑定到当前的version_frame）
            self.version_listbox = tk.Listbox(version_frame, width=60, height=3)
            self.version_listbox.bind('<<ListboxSelect>>', self._on_version_select)
            
            # 填充版本列表
            if self.script_versions:
                for i, version in enumerate(self.script_versions):
                    self.version_listbox.insert(tk.END, f"版本 {i+1}: {version['word_count']}字 ({version['timestamp']})")
            
            self.version_listbox.grid(row=0, column=1, padx=5)
            
            # 字数范围设置
            word_count_frame = ttk.Frame(self.content_frame)
            word_count_frame.grid(row=1, column=0, padx=10, pady=(5, 5), sticky=(tk.W, tk.E))
            
            ttk.Label(word_count_frame, text="脚本字数范围:").grid(row=0, column=0, padx=5)
            
            self.min_words_var = tk.IntVar(value=self.script_word_count["min_words"])
            min_spin = ttk.Spinbox(word_count_frame, from_=100, to=500, textvariable=self.min_words_var, width=6)
            min_spin.grid(row=0, column=1, padx=5)
            
            ttk.Label(word_count_frame, text="~").grid(row=0, column=2)
            
            self.max_words_var = tk.IntVar(value=self.script_word_count["max_words"])
            max_spin = ttk.Spinbox(word_count_frame, from_=150, to=800, textvariable=self.max_words_var, width=6)
            max_spin.grid(row=0, column=3, padx=5)
            
            ttk.Label(word_count_frame, text="字").grid(row=0, column=4, padx=5)
            
            # 音频预配置区域
            audio_config_frame = ttk.LabelFrame(self.content_frame, text="音频预配置", padding="10")
            audio_config_frame.grid(row=2, column=0, padx=10, pady=(5, 5), sticky=(tk.W, tk.E))
            
            # 音色选择（根据IP性别预设）
            ttk.Label(audio_config_frame, text="配音音色：").grid(row=0, column=0, sticky=tk.W, padx=5)
            self.script_voice_combo = ttk.Combobox(audio_config_frame, 
                                                  values=list(self.EDGE_TTS_VOICES.values()), 
                                                  width=30)
            
            # 根据IP性别预设音色
            ip_gender = self.ip_template.get("gender", "女")
            default_voice_key = self._get_default_voice_by_gender(ip_gender)
            voice_keys = list(self.EDGE_TTS_VOICES.keys())
            if default_voice_key in voice_keys:
                default_index = voice_keys.index(default_voice_key)
                self.script_voice_combo.current(default_index)
            else:
                self.script_voice_combo.current(0)
            self.script_voice_combo.grid(row=0, column=1, padx=5)
            
            # 语速选择
            ttk.Label(audio_config_frame, text="语速：").grid(row=0, column=2, sticky=tk.W, padx=5)
            self.script_rate_combo = ttk.Combobox(audio_config_frame, 
                                                 values=["0.8x", "0.9x", "1.0x", "1.1x", "1.2x", "1.3x"], 
                                                 width=10)
            self.script_rate_combo.current(2)  # 默认1.0x
            self.script_rate_combo.grid(row=0, column=3, padx=5)
            
            # 预估时长显示
            ttk.Label(audio_config_frame, text="预估时长：").grid(row=0, column=4, sticky=tk.W, padx=5)
            self.estimated_duration_label = ttk.Label(audio_config_frame, text="--")
            self.estimated_duration_label.grid(row=0, column=5, padx=5)
            
            # 绑定脚本内容变化事件，实时更新预估时长
            def _on_script_change(event):
                self._update_estimated_duration()
            
            # 绑定语速变化事件
            def _on_rate_change(event):
                self._update_estimated_duration()
            
            # 如果script_text已存在，绑定事件
            if hasattr(self, 'script_text'):
                self.script_text.bind('<<Modified>>', _on_script_change)
            
            self.script_rate_combo.bind('<<ComboboxSelected>>', _on_rate_change)
            
            self.script_text.grid(row=3, column=0, padx=10, pady=10)
            
            # 更新预估时长
            self._update_estimated_duration()
        elif self.current_step == 2:
            self.show_storyboard()
        elif self.current_step == 3:
            self.show_images()
        elif self.current_step == 4:
            self.show_audio()
        elif self.current_step == 5:
            self.show_video_result()
    
    def generate_current_step(self):
        self.generate_btn.config(state=tk.DISABLED)
        
        def run_task():
            try:
                if self.current_step == 0:
                    self._generate_topics()
                elif self.current_step == 1:
                    self._generate_script()  # 脚本创作，自动生成基础字幕
                elif self.current_step == 2:
                    self._generate_storyboard()  # 分镜设计，提取金句到字幕
                elif self.current_step == 3:
                    self._generate_images()
                elif self.current_step == 4:
                    self._generate_audio()  # 音频制作，更新字幕时间戳
                elif self.current_step == 5:
                    self._synthesize_video()  # 视频合成
            except Exception as e:
                self.log(f"生成失败: {str(e)}")
                messagebox.showerror("错误", f"生成失败: {str(e)}")
                self.generate_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=run_task, daemon=True).start()
    
    def _generate_topics(self):
        api_key = API_CONFIG.get("minimax", {}).get("api_key", "")
        
        ip_info = ""
        if self.ip_template.get("name"):
            ip_info += f"IP名称：{self.ip_template['name']}\n"
        if self.ip_template.get("track"):
            ip_info += f"赛道：{self.ip_template['track']}\n"
        if self.ip_template.get("target_group"):
            ip_info += f"目标群体：{self.ip_template['target_group']}\n"
        if self.ip_template.get("pain_points"):
            ip_info += f"目标群体痛点：{self.ip_template['pain_points']}\n"
        
        prompt = f"""为家庭教育短视频生成3个选题，请直接输出JSON格式，不要有任何额外文字，不要包含思考过程。

输出格式：
[
    {{"title": "选题标题1", "score": 90, "reason": "推荐理由1"}},
    {{"title": "选题标题2", "score": 85, "reason": "推荐理由2"}},
    {{"title": "选题标题3", "score": 80, "reason": "推荐理由3"}}
]

IP定位信息：
{ip_info if ip_info else "未设置"}

选题要求：
- 贴近目标群体痛点
- 标题吸引眼球，激发点击欲望
- 内容实用，能解决实际问题
- 符合IP定位和赛道方向"""
        
        print("\n" + "="*60)
        
        if not api_key:
            print("[DEBUG] API Key未配置，使用模拟数据")
            self.log("API Key未配置，使用模拟数据生成选题...")
            messagebox.showinfo("提示", "未配置MiniMax API Key，已使用模拟数据生成选题")
            self._generate_mock_topics()
            print("="*60 + "\n")
            return
        
        self.log("正在调用MiniMax Token Plan生成选题...")
        print("[DEBUG] 开始调用MiniMax API生成选题")
        print(f"[DEBUG] Prompt长度: {len(prompt)} 字符")
        
        result = asyncio.run(self.minimax.chat_completion(prompt))
        
        print(f"[DEBUG] API返回结果长度: {len(result) if result else 0} 字符")
        print(f"[DEBUG] API返回内容前200字符: {result[:200] if result else '空'}")
        
        try:
            if result is None:
                print("[ERROR] API调用失败或响应为空")
                self.log("API调用失败，使用模拟数据...")
                messagebox.showinfo("提示", "MiniMax API调用失败，已使用模拟数据生成选题")
                self._generate_mock_topics()
                return
            
            if len(result.strip()) == 0:
                print("[ERROR] API返回内容为空")
                self.log("API返回内容为空，使用模拟数据...")
                messagebox.showinfo("提示", "API返回内容为空，已使用模拟数据")
                self._generate_mock_topics()
                return
            
            result = result.strip()
            
            if '<think>' in result or '&lt;think&gt;' in result:
                print("[DEBUG] 检测到think标签，进行处理...")
                result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
                result = re.sub(r'&lt;think&gt;.*?&lt;/think&gt;', '', result, flags=re.DOTALL)
            
            result = result.strip()
            
            if '```' in result:
                print("[DEBUG] 检测到markdown代码块，进行处理...")
                parts = result.split('```')
                for part in parts:
                    part = part.strip()
                    if part.startswith('json'):
                        result = part[4:].strip()
                        break
                    elif part.startswith('['):
                        result = part
                        break
                else:
                    result = parts[-1].strip()
            
            result = result.strip()
            
            if result.startswith('json'):
                print("[DEBUG] 检测到json标记，进行处理...")
                result = result[4:].strip()
            
            result = result.strip()
            
            result = re.sub(r',\s*([}\]])', r'\1', result)
            print("[DEBUG] 处理尾随逗号")
            
            print(f"[DEBUG] 处理后的内容前150字符: {result[:150]}")
            
            self.generated_topics = json.loads(result)
            print("[DEBUG] JSON解析成功")
            
            if isinstance(self.generated_topics, list) and len(self.generated_topics) >= 3:
                self.topic_listbox.delete(0, tk.END)
                
                for i, topic in enumerate(self.generated_topics[:3]):
                    if isinstance(topic, dict) and 'title' in topic and 'score' in topic and 'reason' in topic:
                        display_text = f"【推荐分 {topic['score']}】{topic['title']} - {topic['reason']}"
                        self.topic_listbox.insert(tk.END, display_text)
                
                self.log(f"成功生成了 {min(len(self.generated_topics), 3)} 个选题")
                self.confirm_btn.config(state=tk.NORMAL)
                self.regenerate_btn.config(state=tk.NORMAL)
                print(f"[DEBUG] 成功显示 {min(len(self.generated_topics), 3)} 个选题")
            else:
                self.log("API返回格式不正确，使用模拟数据...")
                print("[DEBUG] API返回格式不正确，使用模拟数据")
                messagebox.showinfo("提示", "API返回格式不正确，已使用模拟数据")
                self._generate_mock_topics()
        except json.JSONDecodeError as e:
            self.log(f"解析JSON失败: {e}")
            self.log(f"API返回内容: {result[:100]}...")
            self.log("使用模拟数据...")
            print(f"[ERROR] JSON解析失败: {e}")
            print(f"[ERROR] API返回内容: {result[:200]}")
            messagebox.showinfo("提示", "解析选题数据失败，已使用模拟数据")
            self._generate_mock_topics()
        except Exception as e:
            self.log(f"生成选题时发生错误: {e}")
            self.log("使用模拟数据...")
            print(f"[ERROR] 生成选题时发生错误: {e}")
            messagebox.showinfo("提示", "生成选题时发生错误，已使用模拟数据")
            self._generate_mock_topics()
        
        print("="*60 + "\n")
    def _on_version_select(self, event):
        """版本选择事件处理"""
        selected = self.version_listbox.curselection()
        if selected:
            index = selected[0]
            if index < len(self.script_versions):
                version = self.script_versions[index]
                self.current_script["opening"] = version["opening"]
                self.current_script["content"] = version["content"]
                self.current_script["cta"] = version["cta"]
                
                # 更新脚本显示
                self.script_text.delete(1.0, tk.END)
                self.script_text.insert(tk.END, "【开场钩子】\n")
                self.script_text.insert(tk.END, version["opening"] + "\n\n")
                self.script_text.insert(tk.END, "【核心干货】\n")
                self.script_text.insert(tk.END, version["content"] + "\n\n")
                self.script_text.insert(tk.END, "【CTA引导】\n")
                self.script_text.insert(tk.END, version["cta"])
                
                # 更新预估时长
                self._update_estimated_duration()
                
                self.log(f"已切换到版本 {index+1}")
    
    def _generate_mock_topics(self):
        self.generated_topics = [
            {"title": "亲子沟通技巧：如何让孩子愿意跟你说话", "score": 92, "reason": "选题贴近家长痛点，内容实用"},
            {"title": "情绪管理：帮助孩子学会控制情绪", "score": 88, "reason": "需求广泛，教育意义强"},
            {"title": "学习习惯培养：让孩子爱上学习", "score": 85, "reason": "家长关注度高，市场需求大"}
        ]
        
        self.topic_listbox.delete(0, tk.END)
        for i, topic in enumerate(self.generated_topics):
            display_text = f"【推荐分 {topic['score']}】{topic['title']} - {topic['reason']}"
            self.topic_listbox.insert(tk.END, display_text)
        
        self.confirm_btn.config(state=tk.NORMAL)
        self.regenerate_btn.config(state=tk.NORMAL)
    
    def _get_default_voice_by_gender(self, gender: str) -> str:
        """根据IP性别获取默认配音音色"""
        gender_voice_map = {
            "女": "zh-CN-XiaoxiaoNeural",    # 晓晓（女，温柔）
            "男": "zh-CN-YunjianNeural",     # 云健（男，稳重）
            "中性": "zh-CN-XiaoxiaoNeural"   # 默认使用晓晓女声
        }
        return gender_voice_map.get(gender, "zh-CN-XiaoxiaoNeural")
    
    def _estimate_audio_duration(self, text: str, rate: float = 1.0) -> float:
        """根据文本和语速预估配音时长（返回秒）"""
        if not text or not text.strip():
            return 0.0
        
        # 计算有效字数（去除标题、空格和标点符号）
        clean_text = re.sub(r'【.*?】', '', text)
        clean_text = re.sub(r'\s+', '', clean_text)
        # 去除所有标点符号
        clean_text = re.sub(r'[，。！？、；：""''（）《》【】—…·]', '', clean_text)
        char_count = len(clean_text)
        
        # 计算预估时长（中文平均语速约180字/分钟）
        base_chars_per_minute = 180
        adjusted_chars_per_minute = base_chars_per_minute * rate
        if adjusted_chars_per_minute > 0:
            minutes = char_count / adjusted_chars_per_minute
            return minutes * 60
        return 0.0
    
    def _optimize_script_length(self, opening, content, cta, target_words):
        """将脚本优化到指定字数"""
        try:
            api_key = API_CONFIG.get("minimax", {}).get("api_key", "")
            if not api_key:
                return None
            
            prompt = f"""请将以下口播脚本严格精简到{target_words}字以内（不含标点）：

【开场钩子】
{opening}

【核心干货】
{content}

【CTA引导】
{cta}

精简规则：
1. 严格控制总字数在{target_words}字以内
2. 保留开场钩子的吸引力（不超过20字）
3. 保留所有核心观点和实操方法
4. 每个实操方法不超过25字，直接给出可执行动作
5. 删除修饰性描述和重复内容
6. 语言保持口语化，适合口播
7. 直接输出JSON格式，不要有额外文字

输出格式：
{{
    "opening": "精简后的开场钩子",
    "content": "精简后的核心干货",
    "cta": "精简后的CTA引导"
}}"""
            
            print(f"[DEBUG] 调用MiniMax优化脚本字数")
            result = asyncio.run(self.minimax.chat_completion(prompt))
            
            if result:
                result = result.strip()
                if result.startswith('json'):
                    result = result[4:].strip()
                
                data = json.loads(result)
                return {
                    "opening": data.get("opening", ""),
                    "content": data.get("content", ""),
                    "cta": data.get("cta", "")
                }
        except Exception as e:
            print(f"[ERROR] 优化脚本失败: {e}")
        
        return None
    
    def _update_estimated_duration(self):
        """根据脚本内容和语速更新预估时长"""
        if not hasattr(self, 'script_text'):
            return
        
        script_text = self.script_text.get("1.0", tk.END)
        if not script_text.strip():
            self.estimated_duration_label.config(text="--")
            return
        
        # 获取语速
        rate_value = float(self.script_rate_combo.get().replace('x', ''))
        
        # 使用通用的预估函数
        duration = self._estimate_audio_duration(script_text, rate_value)
        self.estimated_duration_label.config(text=f"{duration:.1f}秒")
    
    def _generate_script(self):
        if not self.selected_topic:
            messagebox.showwarning("警告", "请先选择选题")
            return
        
        try:
            min_words = self.min_words_var.get()
            max_words = self.max_words_var.get()
            
            # 验证字数范围
            errors = []
            if min_words < 100:
                errors.append(f"最小字数不能小于100，当前为{min_words}")
                min_words = 100
            if min_words > 500:
                errors.append(f"最小字数不能大于500，当前为{min_words}")
                min_words = 500
            if max_words < 150:
                errors.append(f"最大字数不能小于150，当前为{max_words}")
                max_words = 150
            if max_words > 800:
                errors.append(f"最大字数不能大于800，当前为{max_words}")
                max_words = 800
            if min_words >= max_words:
                errors.append(f"最小字数({min_words})不能大于等于最大字数({max_words})")
                max_words = min_words + 50
            
            # 更新配置
            self.script_word_count["min_words"] = min_words
            self.script_word_count["max_words"] = max_words
            self.min_words_var.set(min_words)
            self.max_words_var.set(max_words)
            
            # 显示警告并阻止继续执行
            if errors:
                messagebox.showwarning("警告", "\n".join(errors) + "\n\n已自动调整为有效范围")
                # 恢复生成按钮状态
                self.generate_btn.config(state=tk.NORMAL)
                return  # 阻止继续调用大模型
                
        except Exception as e:
            print(f"[DEBUG] 获取字数范围失败: {e}")
            min_words = 250
            max_words = 300
        
        api_key = API_CONFIG.get("minimax", {}).get("api_key", "")
        
        print("\n" + "="*60)
        
        if not api_key:
            print("[DEBUG] API Key未配置，使用模拟数据")
            self.log("API Key未配置，使用模拟数据生成脚本...")
            messagebox.showinfo("提示", "未配置MiniMax API Key，已使用模拟数据生成脚本")
            self._generate_mock_script()
            print("="*60 + "\n")
            return
        
        self.log(f"正在调用MiniMax为选题 '{self.selected_topic}' 生成脚本...")
        print("[DEBUG] 开始生成脚本")
        print(f"[DEBUG] 选题: {self.selected_topic}")
        print(f"[DEBUG] 字数范围: {min_words}-{max_words}字")
        
        # 构建IP定位信息
        ip_info = ""
        ip_name = self.ip_template.get("name", "")
        ip_persona = self.ip_template.get("persona", "")
        ip_tone = self.ip_template.get("tone", "专业温和")
        target_group = self.ip_template.get("target_group", "")
        ip_gender = self.ip_template.get("gender", "")
        ip_age = self.ip_template.get("age", "")
        
        if ip_name:
            ip_info += f"IP名称：{ip_name}\n"
        if self.ip_template.get("track"):
            ip_info += f"赛道：{self.ip_template['track']}\n"
        if target_group:
            ip_info += f"目标群体：{target_group}\n"
        if self.ip_template.get("pain_points"):
            ip_info += f"目标群体痛点：{self.ip_template['pain_points']}\n"
        if ip_gender:
            ip_info += f"IP性别：{ip_gender}\n"
        if ip_age:
            ip_info += f"IP年龄：{ip_age}岁\n"
        if ip_persona:
            ip_info += f"IP人设：{ip_persona}\n"
        if ip_tone:
            ip_info += f"语气风格：{ip_tone}\n"
        
        # 根据字数决定结构类型和方法数量范围
        if max_words <= 150:
            structure_type = "短口播版"
            method_range = "1-2个"
            use_pitfalls = False
        elif max_words <= 450:
            structure_type = "中长口播版"
            method_range = "2-3个"
            use_pitfalls = True
        else:
            structure_type = "完整版"
            method_range = "3-5个"
            use_pitfalls = True
        
        # 获取关键词
        keywords = self.ip_template.get("keywords", [])
        keywords_str = ", ".join(keywords) if keywords else "无"
        
        # 构建结构要求
        if max_words <= 150:
            # 短口播版：钩子 → 共情痛点 → 核心原因 → 简单方法 → 短句收尾
            structure_requirements = """1. 开篇钩子（15字内）：直击痛点/反常识/结果前置
2. 共情痛点（25字内）：1-2句场景描述，引发共鸣
3. 核心原因（20字内）：1句话点明根源
4. 简单方法（1-2个，各30字内）：可执行步骤，拒绝空话
5. 短句收尾（20字内）：引导关注"""
            output_format = '''{
    "hook": "开篇钩子内容",
    "empathy": "共情痛点内容",
    "reason": "核心原因",
    "methods": ["方法1", "方法2"],
    "closing": "短句收尾"
}'''
        else:
            # 中长口播版/完整版：钩子 → 场景共鸣 → 根源拆解 → 核心观点 → 分步实操 → 误区避雷 → 价值总结+引导
            # 提前构建条件部分以避免f-string反斜杠问题
            extra_requirements = ""
            if use_pitfalls:
                extra_requirements = "6. 误区避雷：盘点90%人都在踩的错误做法、无效努力\n7. 价值收口+行动引导：短句总结核心+轻引导（收藏/评论/关注）\n"
            
            structure_requirements = f"""1. 开篇黄金钩子（5秒内）：痛点直击/反常识/结果前置，连贯整句
2. 场景深度共情：还原真实生活画面、日常细节，让观众觉得"你懂我"
3. 问题深挖归因：不点表面问题，直击核心根源，用"不是XX，是XX"句式
4. 核心观点输出（{method_range}）：条理清晰、口语化表达，不用专业术语
5. 落地实操方案【高转化核心】：与观点对应，给出可复制、可执行的具体步骤和操作细节
{extra_requirements}"""
            output_format = '''{
    "hook": "开篇钩子内容",
    "empathy": "场景共情内容",
    "attribution": "问题归因内容",
    "core_points": ["核心观点1", "核心观点2"],
    "solutions": ["方案1", "方案2"],
    "pitfalls": ["误区1", "误区2"],
    "closing": "价值收口+引导内容"
}'''
        
        prompt = f"""为{ip_name if ip_name else '家庭教育'}短视频撰写{structure_type}口播脚本，主题：{self.selected_topic}

【IP定位信息】
{ip_info if ip_info else "未设置"}

【字数要求】
- 严格控制在{max_words}字以内（不含标点符号）
- 超出字数将被视为不合格输出
- 钩子（开场）：≤15字，直击痛点/反常识/结果前置
- CTA（结尾）：≤20字，简洁有力的行动引导
- 实操方案：每个不超过30字，直接给出可执行动作
- 中间内容（共情、归因、观点）：根据内容自然分配，保持流畅

【结构要求】
{structure_requirements}

【风格要求】
- 情绪连贯、逻辑顺滑、呼吸感自然
- 拒绝碎片化割裂台词，使用连贯整句
- 符合{ip_tone}的语气风格
- 自然融入热门关键词：{keywords_str}
- 让{target_group if target_group else '观众'}觉得"这就是说我"

【输出格式】
{output_format}"""
        
        print("\n" + "="*80)
        print("[DEBUG] 完整提示词内容:")
        print(prompt)
        print("="*80 + "\n")
        
        print("[DEBUG] 调用MiniMax API...")
        import time
        start_time = time.time()
        result = asyncio.run(self.minimax.chat_completion(prompt))
        elapsed = time.time() - start_time
        print(f"[DEBUG] API调用完成，耗时: {elapsed:.2f}秒")
        
        print("\n" + "="*60)
        print("[DEBUG] 脚本生成结果")
        print(f"[DEBUG] 返回长度: {len(result) if result else 0}")
        print(f"[DEBUG] 返回内容前200字符: {result[:200] if result else '空'}")
        
        try:
            if result is None:
                print("[ERROR] API调用失败或响应为空")
                self.log("API调用失败，使用模拟数据...")
                messagebox.showinfo("提示", "MiniMax API调用失败，已使用模拟数据生成脚本")
                self._generate_mock_script()
                return
            
            if len(result.strip()) == 0:
                print("[ERROR] API返回内容为空")
                self.log("API返回内容为空，使用模拟数据...")
                messagebox.showinfo("提示", "API返回内容为空，已使用模拟数据")
                self._generate_mock_script()
                return
            
            result = result.strip()
            print(f"[DEBUG] 原始内容长度: {len(result)}")
            print(f"[DEBUG] 原始内容前300字符:\n{result[:300]}")
            
            if '<think>' in result.lower():
                print("[DEBUG] 移除think标签（不区分大小写）")
                result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
            
            result = result.strip()
            
            if '&lt;think&gt;' in result:
                print("[DEBUG] 移除HTML实体think标签")
                result = re.sub(r'&lt;think&gt;.*?&lt;/think&gt;', '', result, flags=re.DOTALL)
            
            result = result.strip()
            
            if '```' in result:
                print("[DEBUG] 处理代码块标记")
                parts = result.split('```')
                found_json = False
                for part in parts:
                    part = part.strip()
                    if part.lower().startswith('json'):
                        result = part[4:].strip()
                        found_json = True
                        break
                    elif part.startswith('{') and '}' in part:
                        result = part
                        found_json = True
                        break
            
            result = result.strip()
            
            if result.lower().startswith('json'):
                print("[DEBUG] 移除json标记")
                result = result[4:].strip()
            
            result = result.strip()
            
            result = re.sub(r',\s*([}\]])', r'\1', result)
            print("[DEBUG] 处理尾随逗号")
            
            print(f"[DEBUG] 处理后内容长度: {len(result)}")
            print(f"[DEBUG] 处理后内容:\n{result}")
            
            if not result.startswith('{'):
                print("[ERROR] 处理后内容不是有效的JSON")
                self.log("解析脚本失败，使用模拟数据...")
                messagebox.showinfo("提示", "解析脚本失败，已使用模拟数据")
                self._generate_mock_script()
                return
            
            self.current_script = json.loads(result)
            
            # 兼容新旧三种输出格式
            if "hook" in self.current_script:
                # 新格式：检查是短口播版还是中长口播版
                if "reason" in self.current_script and "methods" in self.current_script:
                    # 短口播版格式：hook → empathy → reason → methods → closing
                    hook = self.current_script.get("hook", "")
                    empathy = self.current_script.get("empathy", "")
                    reason = self.current_script.get("reason", "")
                    methods = self.current_script.get("methods", [])
                    closing = self.current_script.get("closing", "")
                    
                    # 转换为字符串
                    if isinstance(methods, list):
                        methods = "\n".join([f"{i+1}. {m}" for i, m in enumerate(methods)])
                    
                    # 合并为兼容旧格式的结构
                    opening = f"{hook}\n\n{empathy}\n\n{reason}"
                    content = f"【方法技巧】\n{methods}"
                    cta = closing
                    
                    # 保存完整数据
                    self.current_script_full = {
                        "hook": hook,
                        "empathy": empathy,
                        "reason": reason,
                        "methods": methods,
                        "closing": closing
                    }
                else:
                    # 中长口播版/完整版：7段式结构
                    hook = self.current_script.get("hook", "")
                    empathy = self.current_script.get("empathy", "")
                    attribution = self.current_script.get("attribution", "")
                    core_points = self.current_script.get("core_points", [])
                    solutions = self.current_script.get("solutions", [])
                    pitfalls = self.current_script.get("pitfalls", [])
                    closing = self.current_script.get("closing", "")
                    
                    # 转换为字符串
                    if isinstance(core_points, list):
                        core_points = "\n".join([f"{i+1}. {point}" for i, point in enumerate(core_points)])
                    if isinstance(solutions, list):
                        solutions = "\n".join([f"{i+1}. {sol}" for i, sol in enumerate(solutions)])
                    if isinstance(pitfalls, list):
                        pitfalls = "\n".join([f"❌ {p}" for p in pitfalls])
                    
                    # 合并为兼容旧格式的结构
                    opening = f"{hook}\n\n{empathy}\n\n{attribution}"
                    content = f"【核心观点】\n{core_points}\n\n【实操方案】\n{solutions}"
                    if pitfalls:
                        content += f"\n\n【误区避雷】\n{pitfalls}"
                    cta = closing
                    
                    # 保存完整的7段式数据供后续使用
                    self.current_script_full = {
                        "hook": hook,
                        "empathy": empathy,
                        "attribution": attribution,
                        "core_points": core_points,
                        "solutions": solutions,
                        "pitfalls": pitfalls,
                        "closing": closing
                    }
            else:
                # 旧格式：3段式结构
                opening = self.current_script.get("opening", "")
                content = self.current_script.get("content", "")
                cta = self.current_script.get("cta", "")
            
            # 处理列表类型
            if isinstance(opening, list):
                opening = "\n".join(opening)
            if isinstance(content, list):
                content = "\n".join(content)
            if isinstance(cta, list):
                cta = "\n".join(cta)
            
            # 字数处理（排除标点符号）
            total_chars = self._count_effective_chars(opening) + self._count_effective_chars(content) + self._count_effective_chars(cta)
            print(f"[DEBUG] 有效字数: {total_chars}，要求范围: {min_words}-{max_words}")
            
            # 检查字数范围，超过上限10%则发送给大模型优化
            warnings = []
            upper_limit = max_words * 1.1  # 上限10%
            
            if total_chars < min_words:
                warnings.append(f"内容偏少（{total_chars}字），建议重新生成")
            elif total_chars > upper_limit:
                # 超过上限10%，发送给大模型优化
                self.log(f"字数超过上限10%，正在优化...")
                print(f"[DEBUG] 字数超过上限10%，发送给大模型优化")
                
                optimized_script = self._optimize_script_length(opening, content, cta, max_words)
                if optimized_script:
                    opening = optimized_script["opening"]
                    content = optimized_script["content"]
                    cta = optimized_script["cta"]
                    total_chars = self._count_effective_chars(opening) + self._count_effective_chars(content) + self._count_effective_chars(cta)
                    warnings.append(f"已优化至{total_chars}字")
                else:
                    warnings.append(f"内容偏多（{total_chars}字），建议手动精简")
            elif total_chars > max_words:
                warnings.append(f"内容偏多（{total_chars}字），建议重新生成")
            
            # 保存版本
            new_version = {
                "opening": opening,
                "content": content,
                "cta": cta,
                "word_count": total_chars,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            self.script_versions.append(new_version)
            
            # 使用当前脚本
            self.current_script["opening"] = opening
            self.current_script["content"] = content
            self.current_script["cta"] = cta
            
            # 如果有警告，提示用户
            if warnings:
                self.log(f"脚本生成完成（版本{len(self.script_versions)}），{'; '.join(warnings)}")
                print(f"[WARNING] {' | '.join(warnings)}")
            else:
                self.log(f"脚本生成完成（版本{len(self.script_versions)}）")
            
            self.script_text.delete(1.0, tk.END)
            self.script_text.insert(tk.END, "【开场钩子】\n")
            self.script_text.insert(tk.END, opening + "\n\n")
            self.script_text.insert(tk.END, "【核心干货】\n")
            self.script_text.insert(tk.END, content + "\n\n")
            self.script_text.insert(tk.END, "【CTA引导】\n")
            self.script_text.insert(tk.END, cta)
            
            # 统计字数
            self.log(f"脚本生成完成，总字数: {total_chars}字")
            print(f"[DEBUG] 脚本总字数: {total_chars}字")
            
            # 更新预估时长
            self._update_estimated_duration()
            
            self.confirm_btn.config(state=tk.NORMAL)
            self.regenerate_btn.config(state=tk.NORMAL)
            print("[DEBUG] 脚本生成成功")
            
            # 更新UI，刷新版本列表
            self.update_ui()
        except json.JSONDecodeError as e:
            self.log(f"解析脚本失败: {e}")
            print(f"[ERROR] JSON解析失败: {e}")
            print(f"[ERROR] 返回内容: {result[:300]}")
            messagebox.showinfo("提示", "解析脚本失败，已使用模拟数据")
            self._generate_mock_script()
        except Exception as e:
            self.log(f"生成脚本失败: {e}")
            print(f"[ERROR] 生成脚本失败: {e}")
            messagebox.showinfo("提示", "生成脚本失败，已使用模拟数据")
            self._generate_mock_script()
        
        print("="*60 + "\n")
    
    def _generate_mock_script(self):
        scripts = {
            "亲子沟通技巧": {
                "opening": "你是否有过这样的经历？孩子回家一声不吭，问什么都只说'没事'？或者你刚想和孩子聊聊，他却不耐烦地说'别管我'？据调查，超过70%的家长都面临着亲子沟通的困扰。",
                "content": "今天我要分享三个实用的沟通技巧，让你和孩子的对话更顺畅。第一个技巧：'情绪共鸣法'。当孩子闹脾气时，先别急着讲道理，而是说'我知道你现在很生气'，认可他的情绪，孩子才会愿意打开心扉。第二个技巧：'有限选择法'。与其问'你作业写完了吗'，不如说'你是想现在写作业，还是吃完点心后写'？给孩子选择权，他会更有参与感。第三个技巧：'特殊时光'。每天留出15分钟，专注陪孩子做他喜欢的事，不看手机，不批评，只享受彼此的陪伴。",
                "cta": "回顾一下今天的场景：当孩子情绪低落时，我们不再急于说教，而是先共鸣他的情绪；当孩子磨蹭时，我们用有限选择代替催促；当孩子需要关注时，我们用特殊时光建立连接。行动建议：从今天开始，选择一个技巧尝试，坚持一周，你会看到明显的变化。互动提问：你家孩子最让你头疼的沟通问题是什么？欢迎在评论区分享，我们一起讨论解决方法。价值升华：良好的亲子沟通不是天生的，而是需要学习和练习的。当我们用正确的方法与孩子交流，不仅能解决当下的问题，更能为孩子的一生奠定健康的人际关系基础。"
            },
            "三年级是道坎？把握这个关键期，孩子成绩稳居前三": {
                "opening": "为什么孩子一二年级成绩好好的，到了三年级就突然下滑？很多家长都有这样的困惑。其实三年级是孩子学习生涯的第一个分水岭，课程难度增加，学习方法需要升级。",
                "content": "三个方法帮孩子稳稳度过三年级关键期：一、语文每天坚持30分钟阅读，培养阅读理解能力和语感；二、数学注重逻辑思维训练，每天5道应用题练习；三、养成独立作业习惯，设定固定时间和专注环境。",
                "cta": "回顾一下，孩子目前三年级的学习状态如何？行动建议：从今天开始，每天陪伴孩子阅读20分钟，坚持一个月。互动提问：你家孩子在三年级遇到了哪些挑战？欢迎留言分享。价值升华：三年级不是坎，而是成长的阶梯。"
            },
            "用好手机对孩子有用3个优势": {
                "opening": "很多家长视手机为洪水猛兽，但你知道吗？合理使用手机能给孩子带来意想不到的收获。关键在于如何引导，而不是一味禁止。",
                "content": "手机对孩子的三个积极作用：一、拓展学习渠道，在线课程和教育APP让学习更有趣；二、培养信息素养，学会辨别和筛选网络信息；三、增强社交能力，通过视频通话与亲友保持联系。",
                "cta": "回顾今天的内容，手机并非洪水猛兽，关键在于正确引导。行动建议：和孩子一起制定手机使用规则，共同遵守。互动提问：你家孩子每天用手机多长时间？欢迎在评论区分享。价值升华：科技是工具，爱和引导才是教育的核心。"
            }
        }
        
        self.current_script = scripts.get(self.selected_topic, scripts["亲子沟通技巧"])
        self.script_text.delete(1.0, tk.END)
        self.script_text.insert(tk.END, "【开场钩子】\n")
        self.script_text.insert(tk.END, self.current_script.get("opening", "") + "\n\n")
        self.script_text.insert(tk.END, "【核心干货】\n")
        self.script_text.insert(tk.END, self.current_script.get("content", "") + "\n\n")
        self.script_text.insert(tk.END, "【CTA引导】\n")
        self.script_text.insert(tk.END, self.current_script.get("cta", ""))
        
        # 更新预估时长
        self._update_estimated_duration()
        
        self.confirm_btn.config(state=tk.NORMAL)
        self.regenerate_btn.config(state=tk.NORMAL)
    
    def _generate_storyboard(self):
        if not self.current_script:
            messagebox.showwarning("警告", "请先生成脚本")
            self.generate_btn.config(state=tk.NORMAL)
            return
        
        self.log("正在调用MiniMax生成分镜...")
        
        print("\n" + "="*60)
        print("[DEBUG] 开始调用MiniMax API生成分镜")
        
        try:
            result = asyncio.run(self.minimax.generate_storyboard(self.current_script))
        except Exception as e:
            print(f"[ERROR] 调用MiniMax API失败: {e}")
            self.log(f"调用MiniMax API失败: {e}")
            self.log("切换到本地分镜生成...")
            self.current_storyboard = StoryboardGenerator.generate(self.current_script)
            self._update_subtitles_with_golden_lines()
            self._generate_storyboard_subtitles()
            self.log("分镜生成完成（本地）")
            self.show_storyboard()
            self.log(f"生成了 {len(self.current_storyboard)} 个分镜")
            self.confirm_btn.config(state=tk.NORMAL)
            self.regenerate_btn.config(state=tk.NORMAL)
            self.generate_btn.config(state=tk.NORMAL)
            print("="*60 + "\n")
            return
        
        print(f"[DEBUG] 分镜API返回长度: {len(result) if result else 0}")
        print(f"[DEBUG] 分镜API返回内容前200字符: {result[:200] if result else '空'}")
        
        try:
            if result and len(result.strip()) > 0:
                result = result.strip()
                
                if '<think>' in result.lower():
                    print("[DEBUG] 移除think标签")
                    result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
                
                if '```' in result:
                    print("[DEBUG] 处理代码块标记")
                    parts = result.split('```')
                    for part in parts:
                        part = part.strip()
                        if part.lower().startswith('json'):
                            result = part[4:].strip()
                            break
                        elif part.startswith('{'):
                            result = part
                            break
                
                if result.lower().startswith('json'):
                    result = result[4:].strip()
                
                result = re.sub(r',\s*([}\]])', r'\1', result)
                
                print(f"[DEBUG] 处理后分镜内容前100字符: {result[:100]}")
                
                storyboard_data = json.loads(result)
                
                if isinstance(storyboard_data, dict) and 'scenes' in storyboard_data:
                    self.current_storyboard = storyboard_data['scenes']
                    
                    if 'golden_lines' in storyboard_data and storyboard_data['golden_lines']:
                        if hasattr(self, 'current_subtitles') and self.current_subtitles:
                            self.current_subtitles['golden'] = {
                                'text': storyboard_data['golden_lines'][:2],
                                'start': 10.0,
                                'end': 14.0
                            }
                    else:
                        self._update_subtitles_with_golden_lines()
                    
                    self.log("分镜生成完成（MiniMax）")
                else:
                    print("[DEBUG] API返回格式不正确，使用本地生成")
                    self.current_storyboard = StoryboardGenerator.generate(self.current_script)
                    self._update_subtitles_with_golden_lines()
            else:
                print("[DEBUG] API返回为空，使用本地生成")
                self.current_storyboard = StoryboardGenerator.generate(self.current_script)
                self._update_subtitles_with_golden_lines()
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON解析失败: {e}")
            self.log("解析分镜失败，使用本地生成")
            messagebox.showinfo("提示", "分镜API返回格式异常，已切换到本地分镜生成")
            self.current_storyboard = StoryboardGenerator.generate(self.current_script)
            self._update_subtitles_with_golden_lines()
        except Exception as e:
            print(f"[ERROR] 生成分镜失败: {e}")
            self.log(f"生成分镜失败: {e}，使用本地生成")
            messagebox.showinfo("提示", "分镜生成失败，已切换到本地分镜生成")
            self.current_storyboard = StoryboardGenerator.generate(self.current_script)
            self._update_subtitles_with_golden_lines()
        
        # 智能筛选和优化金句
        self._filter_and_optimize_golden_lines()
        
        # 根据分镜生成基础字幕（与分镜强相关）
        self._generate_storyboard_subtitles()
        
        self.log("金句已提取到字幕")
        self.log("基础字幕已根据分镜时长生成")
        
        self.show_storyboard()
        self.log(f"生成了 {len(self.current_storyboard)} 个分镜")
        self.confirm_btn.config(state=tk.NORMAL)
        self.regenerate_btn.config(state=tk.NORMAL)
        
        print("="*60 + "\n")
    
    def _generate_storyboard_subtitles(self):
        """根据分镜生成基础字幕（与分镜强相关）"""
        if not self.current_storyboard or not self.current_script:
            return
        
        # 初始化字幕结构
        if not hasattr(self, 'current_subtitles') or not self.current_subtitles:
            self.current_subtitles = {
                'narration': [],
                'golden': {'text': [], 'start': 0.0, 'end': 0.0}
            }
        
        # 提取所有分镜的旁白内容
        all_narration = []
        golden_lines = []
        current_time = 0.0
        
        # 将脚本按内容块拆分（开场钩子、核心干货各点、CTA引导）
        content_blocks = self._split_script_to_content_blocks()
        print(f"[DEBUG] 内容块数: {len(content_blocks)}")
        
        # 根据内容块优化分镜配置（数量、时长）
        self._optimize_storyboard_for_content(content_blocks)
        
        scene_idx = 0
        block_idx = 0
        
        for scene in self.current_storyboard:
            duration = scene.get('duration', 5)
            
            # 获取分配给当前分镜的内容块
            narration_text = ""
            if block_idx < len(content_blocks):
                narration_text = content_blocks[block_idx].strip()
                if narration_text and not narration_text.endswith('。') and not narration_text.endswith('？') and not narration_text.endswith('！'):
                    narration_text += '。'
            
            # 如果内容块用完了，尝试合并或重复
            if not narration_text and block_idx >= len(content_blocks) and content_blocks:
                narration_text = content_blocks[-1][:50]
            
            scene_idx += 1
            block_idx += 1
            
            if narration_text:
                subtitle_item = {
                    'start': round(current_time, 1),
                    'end': round(current_time + duration, 1),
                    'text': narration_text
                }
                all_narration.append(subtitle_item)
            
            # 提取金句（与该镜头旁白强相关）
            if scene.get('golden_line'):
                golden_lines.append({
                    'text': scene['golden_line'],
                    'start': round(current_time, 1),
                    'end': round(current_time + duration, 1)
                })
            
            current_time += duration
        
        self.current_subtitles['narration'] = all_narration
        
        if golden_lines:
            self.current_subtitles['golden'] = {
                'text': [g['text'] for g in golden_lines],
                'timestamps': [(g['start'], g['end']) for g in golden_lines]
            }
        
        print(f"[DEBUG] 根据分镜生成了 {len(all_narration)} 条旁白字幕")
        print(f"[DEBUG] 提取了 {len(golden_lines)} 条金句")
    
    def _extract_narration_from_description(self, description):
        """从分镜描述中提取旁白内容"""
        if not description:
            return ""
        
        # 尝试从描述中提取旁白部分
        keywords = ['旁白:', '口播:', '讲解:', '说:', '讲解内容:', '旁白内容:']
        for keyword in keywords:
            if keyword in description:
                idx = description.find(keyword)
                result = description[idx + len(keyword):].strip()
                # 移除后续的镜头描述
                for end_mark in ['画面:', '镜头:', '场景:', '【', '】', '(', ')']:
                    if end_mark in result:
                        result = result[:result.find(end_mark)].strip()
                return result
        
        # 如果没有明确的旁白标记，返回描述的前半部分作为旁白
        sentences = description.split('。')
        if len(sentences) > 0:
            return sentences[0] + '。'
        
        return ""
    
    def _split_script_to_paragraphs(self, script):
        """将脚本按段落拆分，返回段落列表"""
        if not script:
            return []
        
        paragraphs = []
        lines = script.split('\n')
        
        current_para = ""
        for line in lines:
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
            
            # 检测标题（以【开头】结尾）
            if line.startswith('【') and line.endswith('】'):
                if current_para.strip():
                    paragraphs.append(current_para.strip())
                    current_para = ""
                continue
            
            # 检测列表项（以数字开头）
            if line[0].isdigit() and (line[1] == '.' or line[1] == '、'):
                if current_para.strip():
                    paragraphs.append(current_para.strip())
            
            # 添加到当前段落
            if current_para:
                current_para += '。' + line
            else:
                current_para = line
        
        if current_para.strip():
            paragraphs.append(current_para.strip())
        
        # 如果没有提取到段落，直接按句号分割
        if not paragraphs:
            sentences = script.replace('。', '。\n').split('\n')
            paragraphs = [s.strip() for s in sentences if s.strip()]
        
        print(f"[DEBUG] 提取到段落: {paragraphs}")
        return paragraphs
    
    def _split_script_to_content_blocks(self):
        """将脚本按内容块拆分：开场钩子、核心干货各点、CTA引导"""
        content_blocks = []
        
        if isinstance(self.current_script, dict):
            opening = self.current_script.get('opening', '').strip()
            content = self.current_script.get('content', '').strip()
            cta = self.current_script.get('cta', '').strip()
            
            # 开场钩子作为一个内容块
            if opening:
                content_blocks.append(opening)
            
            # 核心干货按序号拆分（如1.xxx 2.xxx 3.xxx）
            if content:
                # 按序号拆分
                parts = re.split(r'(?=\d+\.)', content)
                parts = [p.strip() for p in parts if p.strip()]
                
                for part in parts:
                    if part:
                        content_blocks.append(part)
            
            # CTA引导作为一个内容块
            if cta:
                content_blocks.append(cta)
        
        print(f"[DEBUG] 拆分后的内容块: {content_blocks}")
        return content_blocks
    
    def _count_effective_chars(self, text):
        """计算有效字数（排除标点符号）"""
        # 去除标点符号
        clean_text = re.sub(r'[，。！？、；：""''（）《》【】—…·]', '', text)
        return len(clean_text)
    
    def _optimize_storyboard_for_content(self, content_blocks):
        """根据内容块优化分镜配置"""
        if not content_blocks:
            return
        
        # 计算每个内容块的合理时长（8-12字/秒）
        # 获取脚本阶段配置的语速
        if hasattr(self, 'script_rate_combo'):
            rate_value = float(self.script_rate_combo.get().replace('x', ''))
        else:
            rate_value = 1.0
        
        # 使用与脚本预估相同的语速：180字/分钟 * 语速倍率 = 3字/秒 * 语速倍率
        chars_per_second = 3 * rate_value
        
        target_scenes = []
        total_duration = 0
        
        for block in content_blocks:
            # 计算有效字数（排除标点符号）
            char_count = self._count_effective_chars(block)
            # 使用统一的语速计算时长
            duration = round(char_count / chars_per_second, 1)
            # 限制最小和最大时长
            duration = max(3, min(15, duration))
            
            target_scenes.append({
                'content': block,
                'duration': duration
            })
            total_duration += duration
        
        # 确保至少有5个分镜（开场 + 3个干货要点 + CTA）
        MIN_SCENES = 5
        if len(target_scenes) < MIN_SCENES:
            # 拆分大块内容
            expanded_blocks = []
            for block in content_blocks:
                if len(expanded_blocks) >= MIN_SCENES:
                    break
                
                if len(block) > 60:
                    # 按标点符号拆分长内容块
                    sentences = re.split(r'([。！？])', block)
                    chunks = []
                    current_chunk = ""
                    for sentence in sentences:
                        current_chunk += sentence
                        if sentence in ['。', '！', '？']:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                            if len(chunks) >= 2:
                                break
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    
                    # 添加拆分后的块
                    for chunk in chunks[:MIN_SCENES - len(expanded_blocks)]:
                        expanded_blocks.append(chunk)
                else:
                    expanded_blocks.append(block)
            
            # 重新计算时长
            target_scenes = []
            total_duration = 0
            for block in expanded_blocks[:MIN_SCENES]:
                # 计算有效字数（排除标点符号）
                char_count = self._count_effective_chars(block)
                duration = round(char_count / chars_per_second, 1)
                duration = max(3, min(15, duration))
                target_scenes.append({
                    'content': block,
                    'duration': duration
                })
                total_duration += duration
        
        print(f"[DEBUG] 目标分镜数: {len(target_scenes)}, 总时长: {total_duration:.1f}秒")
        
        # 调整现有分镜数量和时长
        num_scenes = len(target_scenes)
        
        # 如果分镜数不够，添加新分镜
        while len(self.current_storyboard) < num_scenes:
            self.current_storyboard.append({
                'id': len(self.current_storyboard) + 1,
                'type': '类型1',
                'duration': 5,
                'description_cn': '',
                'prompt_en': '',
                'golden_line': ''
            })
        
        # 如果分镜数太多，调整到目标数量
        original_count = len(self.current_storyboard)
        if len(self.current_storyboard) > num_scenes:
            self.log(f"[INFO] 分镜数量从 {original_count} 个调整到 {num_scenes} 个")
            print(f"[INFO] 分镜数量从 {original_count} 个调整到 {num_scenes} 个")
            self.current_storyboard = self.current_storyboard[:num_scenes]
        
        # 设置每个分镜的时长
        for i, scene in enumerate(self.current_storyboard):
            if i < len(target_scenes):
                scene['duration'] = target_scenes[i]['duration']
        
        print(f"[DEBUG] 调整后分镜数: {len(self.current_storyboard)}")
    
    def _split_script_to_sentences(self, script):
        """将脚本按句子拆分，返回句子列表（保持原有顺序）"""
        if not script:
            return []
        
        # 确保脚本是字符串
        if isinstance(script, dict):
            script = script.get('content', '')
        
        sentences = []
        
        # 按标题分段处理，保持顺序
        parts = re.split(r'(【.*?】)', script)
        
        print(f"[DEBUG] 脚本分段: {parts}")
        
        for i, part in enumerate(parts):
            if part.startswith('【') and part.endswith('】'):
                continue  # 跳过标题
            
            # 按句号、感叹号、问号拆分
            if part.strip():
                subsentences = re.split(r'([。！？])', part)
                for j in range(0, len(subsentences)-1, 2):
                    sentence = (subsentences[j] + subsentences[j+1]).strip()
                    if sentence:
                        sentences.append(sentence)
        
        print(f"[DEBUG] 拆分后的句子: {sentences}")
        return sentences
    
    def _distribute_sentences_to_scenes(self, sentences, num_scenes):
        """将句子均匀分配给各个分镜（按顺序）"""
        if not sentences:
            return [[] for _ in range(num_scenes)]
        
        result = [[] for _ in range(num_scenes)]
        sentence_idx = 0
        
        print(f"[DEBUG] 开始分配句子，共{len(sentences)}句，分配给{num_scenes}个分镜")
        
        # 按顺序逐个分配句子
        for i in range(num_scenes):
            if sentence_idx < len(sentences):
                result[i].append(sentences[sentence_idx])
                sentence_idx += 1
                print(f"[DEBUG] 分镜{i+1}分配句子: {sentences[i]}")
        
        # 如果还有剩余句子，继续分配
        while sentence_idx < len(sentences):
            for i in range(num_scenes):
                if sentence_idx < len(sentences):
                    result[i].append(sentences[sentence_idx])
                    sentence_idx += 1
        
        print(f"[DEBUG] 分配结果: {result}")
        return result
    
    def _ensure_enough_sentences(self, sentences, num_scenes):
        """确保有足够的句子分配给每个分镜，必要时拆分长句"""
        if not sentences:
            return [[] for _ in range(num_scenes)]
        
        # 如果句子数量足够，直接分配
        if len(sentences) >= num_scenes:
            return self._distribute_sentences_to_scenes(sentences, num_scenes)
        
        # 如果句子不够，先尝试拆分长句
        expanded_sentences = []
        for sentence in sentences:
            if len(sentence) > 30:  # 如果句子较长，尝试拆分
                # 按逗号、顿号、分号拆分
                parts = re.split(r'[,，；;、]', sentence)
                parts = [p.strip() for p in parts if p.strip()]
                
                if len(parts) > 1:
                    # 为拆分后的每个部分添加标点
                    for i, part in enumerate(parts):
                        if i < len(parts) - 1:
                            expanded_sentences.append(part + '，')
                        else:
                            # 最后一部分保留原句的标点
                            expanded_sentences.append(part + sentence[-1])
                else:
                    expanded_sentences.append(sentence)
            else:
                expanded_sentences.append(sentence)
        
        print(f"[DEBUG] 拆分后句子数: {len(expanded_sentences)}")
        
        # 如果拆分后还是不够，重复使用内容
        if len(expanded_sentences) < num_scenes:
            while len(expanded_sentences) < num_scenes:
                # 重复最短的句子，避免内容过长
                shortest_idx = min(range(len(expanded_sentences)), key=lambda i: len(expanded_sentences[i]))
                expanded_sentences.append(expanded_sentences[shortest_idx])
        
        return self._distribute_sentences_to_scenes(expanded_sentences, num_scenes)
    
    def _optimize_scene_durations(self, script_text):
        """根据脚本字数优化分镜时长"""
        if not script_text or not self.current_storyboard:
            return
        
        # 计算脚本字数（去除标题和空格）
        text = re.sub(r'【.*?】', '', script_text)
        text = re.sub(r'\s', '', text)
        char_count = len(text)
        
        # 计算目标时长（语速约2.8字/秒，适合短视频）
        target_duration = char_count / 2.8
        print(f"[DEBUG] 脚本字数: {char_count}，目标时长: {target_duration:.1f}秒")
        
        # 获取当前总时长
        current_total = sum(scene.get('duration', 5) for scene in self.current_storyboard)
        
        # 如果差异超过10秒，进行调整
        if abs(target_duration - current_total) > 10:
            # 计算缩放因子
            scale_factor = target_duration / current_total
            
            # 调整每个分镜的时长（限制在合理范围内）
            for scene in self.current_storyboard:
                original_duration = scene.get('duration', 5)
                new_duration = max(3, min(12, original_duration * scale_factor))
                scene['duration'] = round(new_duration, 1)
            
            new_total = sum(scene.get('duration', 5) for scene in self.current_storyboard)
            print(f"[DEBUG] 优化后总时长: {new_total:.1f}秒")
    
    def _is_high_quality_golden_line(self, text):
        """评估金句质量"""
        if not text or len(text) < 8:
            return False
        
        # 检查关键词
        keywords = ['核心', '关键', '秘诀', '真相', '本质', '方法', '技巧', '智慧', '重要', '学会', '掌握']
        has_keyword = any(keyword in text for keyword in keywords)
        
        # 检查冲击力特征
        has_impact = any([
            '？' in text,                    # 反问
            '！' in text,                    # 感叹
            any(c.isdigit() for c in text),  # 数字
            '不是' in text and '而是' in text,  # 对比
            '只有' in text or '只要' in text   # 条件
        ])
        
        # 检查长度
        is_proper_length = 8 <= len(text) <= 35
        
        return (has_keyword or has_impact) and is_proper_length
    
    def _extract_golden_lines_from_script(self):
        """从脚本中提取高质量金句"""
        full_text = self.current_script.get("opening", "") + "\n" + \
                    self.current_script.get("content", "") + "\n" + \
                    self.current_script.get("cta", "")
        
        # 按句子拆分
        sentences = re.split(r'([。！？])', full_text)
        sentences = [s.strip() for s in sentences if s.strip() and s not in ['。', '！', '？']]
        
        # 筛选高质量句子
        golden_lines = []
        for sentence in sentences:
            if self._is_high_quality_golden_line(sentence):
                golden_lines.append(sentence)
                if len(golden_lines) >= 3:
                    break
        
        return golden_lines
    
    def _filter_and_optimize_golden_lines(self):
        """智能筛选和优化金句"""
        if not self.current_storyboard:
            return []
        
        # 收集大模型生成的金句并进行质量筛选
        high_quality_lines = []
        for scene in self.current_storyboard:
            gl = scene.get('golden_line', '').strip()
            if gl:
                if self._is_high_quality_golden_line(gl):
                    high_quality_lines.append(gl)
                else:
                    # 低质量金句，清空
                    scene['golden_line'] = ""
        
        # 兜底机制（如果高质量金句少于1条）
        if len(high_quality_lines) < 1:
            extracted_lines = self._extract_golden_lines_from_script()
            # 分配给关键分镜（开头、中间、结尾）
            key_indices = [0, len(self.current_storyboard)//2, len(self.current_storyboard)-1]
            for i, idx in enumerate(key_indices):
                if i < len(extracted_lines) and idx < len(self.current_storyboard):
                    self.current_storyboard[idx]['golden_line'] = extracted_lines[i]
                    high_quality_lines.append(extracted_lines[i])
        
        print(f"[DEBUG] 优化后金句数量: {len(high_quality_lines)}")
        return high_quality_lines[:3]  # 最多保留3条
    
    def _update_subtitles_with_golden_lines(self):
        """从分镜中提取金句并更新字幕（不限制数量，与内容强相关）"""
        if not hasattr(self, 'current_subtitles') or not self.current_subtitles:
            return
        
        golden_lines = []
        timestamps = []
        current_time = 0.0
        
        for scene in self.current_storyboard:
            duration = scene.get('duration', 5)
            if scene.get('golden_line'):
                golden_lines.append(scene['golden_line'])
                timestamps.append((round(current_time, 1), round(current_time + duration, 1)))
            current_time += duration
        
        if golden_lines:
            self.current_subtitles['golden'] = {
                'text': golden_lines,  # 不限制数量，全部保留
                'timestamps': timestamps
            }
    
    def show_storyboard(self):
        for widget in self.content_frame.winfo_children():
            widget.grid_remove()
        
        # ========== 第一部分：分镜概览 ==========
        overview_frame = ttk.LabelFrame(self.content_frame, text="📋 分镜概览")
        overview_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky=(tk.W, tk.E))
        
        # 统计信息
        total_duration = sum(scene['duration'] for scene in self.current_storyboard)
        golden_count = sum(1 for scene in self.current_storyboard if scene.get('golden_line'))
        
        stats_frame = ttk.Frame(overview_frame)
        stats_frame.grid(row=0, column=0, padx=10, pady=5)
        
        ttk.Label(stats_frame, text=f"📸 分镜数量: {len(self.current_storyboard)}").grid(row=0, column=0, padx=20)
        ttk.Label(stats_frame, text=f"⏱️ 总时长: {total_duration}秒").grid(row=0, column=1, padx=20)
        ttk.Label(stats_frame, text=f"⭐ 金句数量: {golden_count}").grid(row=0, column=2, padx=20)
        
        # ========== 第二部分：金句汇总 ==========
        golden_frame = ttk.LabelFrame(self.content_frame, text="⭐ 金句汇总（与内容强相关）")
        golden_frame.grid(row=1, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))
        
        golden_lines = []
        for scene in self.current_storyboard:
            if scene.get('golden_line'):
                golden_lines.append((scene['id'], scene['golden_line']))
        
        if golden_lines:
            golden_text = "\n".join([f"📌 镜头{id}: {line}" for id, line in golden_lines])
        else:
            golden_text = "暂无金句"
        
        self.golden_text = scrolledtext.ScrolledText(golden_frame, width=90, height=4)
        self.golden_text.insert(tk.END, golden_text)
        self.golden_text.config(state=tk.DISABLED)
        self.golden_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # ========== 第三部分：分镜列表 ==========
        tree_frame = ttk.LabelFrame(self.content_frame, text="🎬 分镜列表")
        tree_frame.grid(row=2, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))
        
        # 创建treeview（只显示关键信息）
        tree = ttk.Treeview(tree_frame, columns=('id', 'type', 'duration', 'desc'), height=6)
        tree.heading('#0', text='')
        tree.heading('id', text='编号')
        tree.heading('type', text='类型')
        tree.heading('duration', text='时长')
        tree.heading('desc', text='描述')
        
        tree.column('#0', width=0, stretch=tk.NO)
        tree.column('id', width=40, anchor=tk.CENTER)
        tree.column('type', width=60, anchor=tk.CENTER)
        tree.column('duration', width=50, anchor=tk.CENTER)
        tree.column('desc', width=350)
        
        # 插入数据
        for scene in self.current_storyboard:
            tree.insert('', tk.END, values=(
                scene['id'],
                scene['type'],
                f"{scene['duration']}s",
                scene['description_cn'][:35] + "..." if len(scene['description_cn']) > 35 else scene['description_cn']
            ))
        
        # 放置treeview
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 添加垂直滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 设置tree_frame高度
        tree_frame.config(height=180)
        
        # ========== 第四部分：选中分镜详情 ==========
        detail_frame = ttk.LabelFrame(self.content_frame, text="🔍 选中分镜详情")
        detail_frame.grid(row=3, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))
        detail_frame.grid_columnconfigure(0, weight=1)
        
        # 画面描述
        desc_label = ttk.Label(detail_frame, text="画面描述：")
        desc_label.grid(row=0, column=0, sticky=tk.W)
        self.desc_text = scrolledtext.ScrolledText(detail_frame, width=75, height=2)
        self.desc_text.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # 字幕预览（与画面强相关）
        subtitle_label = ttk.Label(detail_frame, text="旁白字幕：")
        subtitle_label.grid(row=2, column=0, sticky=tk.W)
        self.subtitle_text = scrolledtext.ScrolledText(detail_frame, width=75, height=2)
        self.subtitle_text.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # 英文提示词（折叠显示，需要时展开）
        prompt_frame = ttk.Frame(detail_frame)
        prompt_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=2)
        
        def toggle_prompt():
            if self.prompt_text.winfo_viewable():
                self.prompt_text.grid_remove()
                prompt_toggle.config(text="展开提示词")
            else:
                self.prompt_text.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=2)
                prompt_toggle.config(text="收起提示词")
        
        prompt_toggle = ttk.Button(prompt_frame, text="展开提示词", command=toggle_prompt)
        prompt_toggle.grid(row=0, column=0, sticky=tk.W)
        
        self.prompt_text = scrolledtext.ScrolledText(detail_frame, width=75, height=3)
        # 默认隐藏提示词
        
        def update_detail(idx):
            """更新选中分镜的详情"""
            scene = self.current_storyboard[idx]
            
            # 更新画面描述
            self.desc_text.delete(1.0, tk.END)
            self.desc_text.insert(tk.END, scene['description_cn'])
            
            # 更新提示词
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(tk.END, scene['prompt_en'])
            
            # 更新字幕预览（从current_subtitles中获取正确的旁白内容）
            self.subtitle_text.delete(1.0, tk.END)
            if hasattr(self, 'current_subtitles') and self.current_subtitles.get('narration'):
                start_time = sum(s['duration'] for s in self.current_storyboard[:idx])
                end_time = start_time + scene['duration']
                
                # 查找对应时间段的字幕
                found_subtitle = None
                for sub in self.current_subtitles['narration']:
                    if sub['start'] >= start_time - 0.5 and sub['start'] < end_time:
                        found_subtitle = sub
                        break
                
                if found_subtitle:
                    self.subtitle_text.insert(tk.END, f"[{found_subtitle['start']}s - {found_subtitle['end']}s] {found_subtitle['text']}")
                else:
                    # 如果没有找到对应字幕，显示提示
                    self.subtitle_text.insert(tk.END, f"[{start_time}s - {end_time}s] 暂无对应旁白字幕")
            else:
                start_time = sum(s['duration'] for s in self.current_storyboard[:idx])
                end_time = start_time + scene['duration']
                self.subtitle_text.insert(tk.END, f"[{start_time}s - {end_time}s] 字幕尚未生成")
        
        def on_select(event):
            selected = tree.selection()
            if selected:
                idx = int(tree.item(selected[0], 'values')[0]) - 1
                update_detail(idx)
        
        tree.bind('<<TreeviewSelect>>', on_select)
        
        # 默认选中第一个分镜并显示详情
        if self.current_storyboard:
            tree.selection_set(tree.get_children()[0])
            update_detail(0)
        
        # 设置可滚动区域
        self.content_frame.grid_rowconfigure(2, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
    
    def _generate_images(self):
        if not self.current_storyboard:
            messagebox.showwarning("警告", "请先生成分镜")
            return
        
        self.log("正在调用MiniMax image-01生成图片...")
        self.generated_images = []
        
        width = self.selected_resolution.get("width", 1080)
        height = self.selected_resolution.get("height", 1920)
        size_str = f"{width}*{height}"
        
        for i, scene in enumerate(self.current_storyboard):
            self.log(f"生成图片 {i+1}/{len(self.current_storyboard)}...")
            image_path = asyncio.run(self.minimax.generate_image(scene['prompt_en'], size_str))
            
            if not image_path:
                image_path = asyncio.run(self.qwen_image.generate_image(scene['prompt_en'], size_str))
            
            if image_path:
                self.generated_images.append(image_path)
        
        self.show_images()
        self.log(f"生成了 {len(self.generated_images)} 张图片")
        self.confirm_btn.config(state=tk.NORMAL)
        self.regenerate_btn.config(state=tk.NORMAL)
    
    def show_images(self):
        for widget in self.content_frame.winfo_children():
            widget.grid_remove()
        
        if not self.generated_images:
            ttk.Label(self.content_frame, text="暂无图片").grid(row=0, column=0)
            return
        
        print(f"[DEBUG] 图片列表: {self.generated_images}")
        
        # 场景选择和重新生成按钮（放在上方）
        top_frame = ttk.Frame(self.content_frame)
        top_frame.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.image_var = tk.StringVar()
        image_options = [f"场景 {i+1}" for i in range(len(self.generated_images))]
        image_combo = ttk.Combobox(top_frame, textvariable=self.image_var, values=image_options, width=15)
        image_combo.current(0)
        image_combo.pack(side=tk.LEFT, padx=5)
        
        self.regenerate_single_btn = ttk.Button(top_frame, text="重新生成当前图片", 
                                               command=self._regenerate_single_image)
        self.regenerate_single_btn.pack(side=tk.LEFT, padx=5)
        
        # 图片显示区域
        self.image_label = ttk.Label(self.content_frame)
        self.image_label.grid(row=1, column=0, pady=10)
        
        # 描述和提示词
        ttk.Label(self.content_frame, text="中文描述：").grid(row=2, column=0, sticky=tk.W)
        self.image_desc_cn = scrolledtext.ScrolledText(self.content_frame, width=60, height=2)
        self.image_desc_cn.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(self.content_frame, text="英文提示词：").grid(row=4, column=0, sticky=tk.W)
        self.image_prompt_text = scrolledtext.ScrolledText(self.content_frame, width=60, height=3)
        self.image_prompt_text.grid(row=5, column=0, sticky=(tk.W, tk.E))
        
        def load_image(idx):
            if idx < len(self.generated_images):
                image_path = self.generated_images[idx]
                print(f"[DEBUG] 加载图片: {image_path}")
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(image_path)
                    img.thumbnail((400, 400))
                    self.photo = ImageTk.PhotoImage(img)
                    self.image_label.config(image=self.photo)
                    self.image_label.image = self.photo  # 保持引用
                except Exception as e:
                    print(f"加载图片失败: {e}")
                    self.image_label.config(text=f"加载图片失败: {e}")
        
        if self.current_storyboard:
            print(f"[DEBUG] 分镜数据存在，数量: {len(self.current_storyboard)}")
            print(f"[DEBUG] 第1个分镜提示词: {self.current_storyboard[0].get('prompt_en', '空')}")
            self.image_desc_cn.insert(tk.END, self.current_storyboard[0]['description_cn'])
            self.image_prompt_text.insert(tk.END, self.current_storyboard[0]['prompt_en'])
            load_image(0)
        else:
            print("[DEBUG] 分镜数据为空")
        
        def on_select(event):
            idx = image_combo.current()
            print(f"[DEBUG] 切换到场景 {idx+1}")
            if idx < len(self.current_storyboard):
                self.image_desc_cn.delete(1.0, tk.END)
                self.image_desc_cn.insert(tk.END, self.current_storyboard[idx]['description_cn'])
                self.image_prompt_text.delete(1.0, tk.END)
                self.image_prompt_text.insert(tk.END, self.current_storyboard[idx]['prompt_en'])
                load_image(idx)
            else:
                print(f"[DEBUG] 场景索引 {idx} 超出范围")
        
        image_combo.bind('<<ComboboxSelected>>', on_select)
    
    def _regenerate_single_image(self):
        idx = self.image_var.get().split()[1]
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(self.current_storyboard):
                self.log(f"重新生成图片 {idx+1}/{len(self.current_storyboard)}...")
                prompt = self.current_storyboard[idx]['prompt_en']
                
                width = self.selected_resolution.get("width", 1080)
                height = self.selected_resolution.get("height", 1920)
                size_str = f"{width}*{height}"
                
                image_path = asyncio.run(self.qwen_image.generate_image(prompt, size_str))
                if image_path:
                    self.generated_images[idx] = image_path
                    self.log(f"图片 {idx+1} 重新生成成功")
                else:
                    self.log(f"图片 {idx+1} 重新生成失败")
        except Exception as e:
            self.log(f"重新生成图片失败: {e}")
            print(f"[ERROR] 重新生成图片失败: {e}")
    
    def _generate_audio(self):
        if not self.current_script:
            messagebox.showwarning("警告", "请先生成脚本")
            return
        
        full_text = self.current_script.get("opening", "") + \
                    self.current_script.get("content", "") + \
                    self.current_script.get("cta", "")
        
        # 获取脚本阶段配置的音色（优先使用脚本阶段的配置）
        if hasattr(self, 'script_voice_combo'):
            idx = self.script_voice_combo.current()
            self.selected_voice = list(self.EDGE_TTS_VOICES.keys())[idx]
            self.log(f"使用脚本阶段配置的音色: {self.EDGE_TTS_VOICES[self.selected_voice]}")
        elif hasattr(self, 'voice_combo'):
            idx = self.voice_combo.current()
            self.selected_voice = list(self.EDGE_TTS_VOICES.keys())[idx]
            self.log(f"使用音频阶段配置的音色: {self.EDGE_TTS_VOICES[self.selected_voice]}")
        
        # 获取脚本阶段配置的语速
        if hasattr(self, 'script_rate_combo'):
            self.selected_rate = float(self.script_rate_combo.get().replace('x', ''))
            self.log(f"使用脚本阶段配置的语速: {self.selected_rate}x")
        else:
            self.selected_rate = 1.0
        
        # 根据语速预测时长，用于背景音乐生成
        estimated_duration = self._estimate_audio_duration(full_text, self.selected_rate)
        self.log(f"预测配音时长: {estimated_duration:.1f}秒")
        
        self.log("正在使用edge-tts生成配音...")
        self.audio_path = self._generate_audio_edge_tts(full_text, self.selected_rate)
        
        if self.audio_path:
            self.log(f"配音生成成功: {self.audio_path}")
        else:
            self.log("配音生成失败")
        
        self.log("正在调用MiniMax Music-2.6生成背景音乐...")
        emotion = "warm gentle positive"
        self.bgm_path = asyncio.run(self.minimax.generate_music(emotion))
        
        if self.bgm_path:
            self.log(f"背景音乐生成成功: {self.bgm_path}")
        else:
            self.log("背景音乐生成失败（未配置API或达到每日配额）")
        
        self._update_subtitle_timestamps()  # 根据音频时长更新字幕时间戳
        self.log("字幕时间戳已更新")
        
        self.show_audio()
        self.regenerate_btn.config(state=tk.NORMAL)
        
        # 只有配音生成成功才能进入下一步
        if self.audio_path:
            self.confirm_btn.config(state=tk.NORMAL)
        else:
            messagebox.showwarning("警告", "配音生成失败，请检查配置后重新生成")
            self.confirm_btn.config(state=tk.DISABLED)
    
    def _update_subtitle_timestamps(self):
        """根据音频时长更新字幕时间戳"""
        if not hasattr(self, 'current_subtitles') or not self.current_subtitles:
            return
        
        if not self.audio_path:
            return
        
        audio_duration = VideoComposer._get_audio_duration(self.audio_path)
        narrator_subs = self.current_subtitles.get('narrator', [])
        
        if narrator_subs:
            total_duration = sum(sub.get('end', 0) - sub.get('start', 0) for sub in narrator_subs)
            if total_duration > 0 and audio_duration > 0:
                scale_factor = audio_duration / total_duration
                
                for sub in narrator_subs:
                    if 'start' in sub:
                        sub['start'] = round(sub['start'] * scale_factor, 2)
                    if 'end' in sub:
                        sub['end'] = round(sub['end'] * scale_factor, 2)
    
    def _generate_audio_edge_tts(self, text: str, rate: float = None) -> str:
        try:
            import edge_tts
            import asyncio
            import os
            import time
            import shutil
            
            voice = getattr(self, 'selected_voice', 'zh-CN-YunxiNeural')
            
            # 优先使用传入的语速参数，否则从界面获取
            if rate is not None:
                rate_value = rate
            elif hasattr(self, 'script_rate_combo'):
                rate_value = float(self.script_rate_combo.get().replace('x', ''))
            elif hasattr(self, 'rate_combo'):
                rate_value = float(self.rate_combo.get().replace('x', ''))
            else:
                rate_value = 1.0
            rate_percent = f"+{int((rate_value - 1) * 100)}%"
            
            output_path = "audio/voice.mp3"
            temp_path = "audio/voice_temp.mp3"
            
            # 确保停止任何正在播放的音频，释放文件占用
            self._stop_audio()
            
            # 删除可能存在的临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            print(f"[DEBUG] 开始生成配音，文本长度: {len(text)}")
            print(f"[DEBUG] 使用音色: {voice}, 语速: {rate_percent}")
            self.log(f"正在使用Edge-TTS生成配音，音色: {self.EDGE_TTS_VOICES.get(voice, voice)}")
            
            start_time = time.time()
            communicate = edge_tts.Communicate(text, voice, rate=rate_percent)
            asyncio.run(communicate.save(temp_path))
            elapsed_time = time.time() - start_time
            
            print(f"[DEBUG] Edge-TTS调用耗时: {elapsed_time:.2f}秒")
            
            # 验证生成的文件是否有效
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                file_size = os.path.getsize(temp_path)
                # 将临时文件移动到最终位置
                shutil.move(temp_path, output_path)
                print(f"[DEBUG] 配音生成成功: {output_path}, 大小: {file_size} bytes, 耗时: {elapsed_time:.2f}秒")
                self.log(f"Edge-TTS配音生成成功，耗时: {elapsed_time:.2f}秒，文件大小: {file_size} bytes")
                
                # 检查是否选择了女声但当前可能返回男声
                if voice in self.FEMALE_VOICES and voice == "zh-CN-YunxiNeural":
                    self.log("⚠️ 注意：当前Edge-TTS服务的云希女声可能返回男声，如不满意可尝试其他语音")
                
                return output_path
            else:
                print(f"[DEBUG] Edge-TTS生成的文件为空或不存在")
                raise Exception("生成的音频文件为空")
                
        except Exception as e:
            error_msg = f"Edge-TTS生成失败: {type(e).__name__}: {str(e)[:100]}"
            print(f"[ERROR] {error_msg}")
            self.log(f"Edge-TTS生成失败: {error_msg}")
            
            # 尝试所有同性别备用语音
            backup_voices_tried = []
            backup_voice = self._get_backup_voice(voice)
            while backup_voice and backup_voice != voice and backup_voice not in backup_voices_tried:
                backup_voices_tried.append(backup_voice)
                self.log(f"正在尝试备用音色: {self.EDGE_TTS_VOICES.get(backup_voice, backup_voice)}")
                result = self._generate_audio_with_voice(text, backup_voice, rate_percent)
                if result:
                    return result
                backup_voice = self._get_next_backup_voice(voice, backup_voices_tried)
            
            # 如果选择的是女声但所有女声都失败了
            if voice in self.FEMALE_VOICES:
                self.log("⚠️ 所有女声语音都不可用，将尝试男声语音")
                # 尝试男声
                for male_voice in self.MALE_VOICES:
                    self.log(f"正在尝试男声音色: {self.EDGE_TTS_VOICES.get(male_voice, male_voice)}")
                    result = self._generate_audio_with_voice(text, male_voice, rate_percent)
                    if result:
                        self.log("⚠️ 已使用男声生成配音（女声不可用）")
                        return result
            
            self.log(f"Edge-TTS生成失败，正在尝试备用方案(gTTS)...")
            # 尝试使用gTTS备用方案
            result = self._generate_audio_gtts(text)
            if result:
                return result
            
            self.log(f"gTTS生成失败，正在尝试备用方案(pyttsx3)...")
            # 尝试使用pyttsx3备用方案
            return self._generate_audio_backup(text)
    
    def _get_backup_voice(self, preferred_voice):
        """获取备用语音，保持性别一致"""
        if preferred_voice in self.FEMALE_VOICES:
            # 返回另一个可用的女声
            for v in self.FEMALE_VOICES:
                if v != preferred_voice:
                    return v
        elif preferred_voice in self.MALE_VOICES:
            # 返回另一个可用的男声
            for v in self.MALE_VOICES:
                if v != preferred_voice:
                    return v
        return None
    
    def _get_next_backup_voice(self, preferred_voice, tried_voices):
        """获取下一个备用语音，跳过已尝试的"""
        if preferred_voice in self.FEMALE_VOICES:
            for v in self.FEMALE_VOICES:
                if v != preferred_voice and v not in tried_voices:
                    return v
        elif preferred_voice in self.MALE_VOICES:
            for v in self.MALE_VOICES:
                if v != preferred_voice and v not in tried_voices:
                    return v
        return None
    
    def _generate_audio_with_voice(self, text: str, voice: str, rate_percent: str) -> str:
        """使用指定语音生成配音"""
        try:
            import edge_tts
            import asyncio
            import os
            import shutil
            
            output_path = "audio/voice.mp3"
            temp_path = "audio/voice_temp.mp3"
            
            # 删除可能存在的临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            communicate = edge_tts.Communicate(text, voice, rate=rate_percent)
            asyncio.run(communicate.save(temp_path))
            
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                shutil.move(temp_path, output_path)
                print(f"[DEBUG] 使用备用语音 {voice} 生成成功")
                self.log(f"使用备用音色 {self.EDGE_TTS_VOICES.get(voice, voice)} 生成成功")
                return output_path
            else:
                print(f"[DEBUG] 备用语音 {voice} 生成的文件为空")
                return ""
        except Exception as e:
            print(f"[ERROR] 使用备用语音 {voice} 生成失败: {e}")
            return ""
    
    def _generate_audio_gtts(self, text: str) -> str:
        """使用gTTS生成配音（备用方案）"""
        try:
            from gtts import gTTS
            import os
            import shutil
            
            output_path = "audio/voice.mp3"
            temp_path = "audio/voice_temp.mp3"
            
            # 删除可能存在的临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            print(f"[DEBUG] 使用gTTS生成配音")
            self.log(f"正在使用gTTS生成配音...")
            
            # 使用中文女声
            tts = gTTS(text=text, lang='zh-CN', slow=False)
            tts.save(temp_path)
            
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                shutil.move(temp_path, output_path)
                file_size = os.path.getsize(output_path)
                print(f"[DEBUG] gTTS配音生成成功: {output_path}, 大小: {file_size} bytes")
                self.log(f"gTTS配音生成成功，文件大小: {file_size} bytes")
                self.log("⚠️ 使用gTTS生成配音（Edge-TTS不可用）")
                return output_path
            else:
                print(f"[DEBUG] gTTS生成的文件为空")
                return ""
        except Exception as e:
            print(f"[ERROR] gTTS生成失败: {type(e).__name__}: {e}")
            return ""
    
    def _generate_audio_backup(self, text: str) -> str:
        """备用配音生成方案(pyttsx3)"""
        try:
            import pyttsx3
            import os
            import shutil
            
            output_path = "audio/voice.mp3"
            temp_path = "audio/voice_temp.mp3"
            
            # 删除可能存在的临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            # 获取用户选择的音色，确定目标性别
            selected_voice_key = getattr(self, 'selected_voice', 'zh-CN-YunxiNeural')
            target_gender = 'female' if selected_voice_key in ['zh-CN-YunxiNeural', 'zh-CN-XiaoyouNeural', 
                                                               'zh-CN-XiaochenNeural', 'zh-CN-XiaohanNeural', 
                                                               'zh-CN-XiaomengNeural'] else 'male'
            
            print(f"[DEBUG] 备用TTS - 用户选择音色: {selected_voice_key}, 目标性别: {target_gender}")
            print(f"[DEBUG] 系统可用语音数量: {len(voices)}")
            
            # 尝试选择中文语音（兼容不同版本的pyttsx3）
            # 优先选择匹配用户选择音色性别的语音
            chinese_voice_found = False
            preferred_voices = []
            other_voices = []
            
            for i, voice in enumerate(voices):
                try:
                    lang = getattr(voice, 'language', 'unknown')
                    voice_id = getattr(voice, 'id', 'unknown')
                    voice_name = getattr(voice, 'name', 'unknown')
                    gender = getattr(voice, 'gender', 'unknown')
                    
                    print(f"[DEBUG] 语音 {i}: id={voice_id}, lang={lang}, name={voice_name}, gender={gender}")
                    
                    if lang and 'zh' in lang.lower():
                        # 检查性别属性
                        is_female = False
                        if hasattr(voice, 'gender'):
                            is_female = voice.gender == 'female' or str(voice.gender).lower() == '1'
                        elif hasattr(voice, 'id'):
                            is_female = 'female' in voice.id.lower() or 'girl' in voice.id.lower() or 'woman' in voice.id.lower()
                        
                        if (target_gender == 'female' and is_female) or (target_gender == 'male' and not is_female):
                            preferred_voices.append(voice)
                        else:
                            other_voices.append(voice)
                except Exception as ve:
                    print(f"[DEBUG] 检查语音 {i} 时出错: {ve}")
                    if hasattr(voice, 'id') and 'zh' in voice.id.lower():
                        other_voices.append(voice)
            
            # 优先使用匹配性别的语音
            all_candidates = preferred_voices + other_voices
            selected_voice_info = ""
            
            if preferred_voices:
                engine.setProperty('voice', preferred_voices[0].id)
                chinese_voice_found = True
                selected_voice_info = f"匹配性别语音: {preferred_voices[0].id}"
                print(f"[DEBUG] 备用TTS选择匹配性别的语音: {preferred_voices[0].id}")
            elif other_voices:
                engine.setProperty('voice', other_voices[0].id)
                chinese_voice_found = True
                selected_voice_info = f"非匹配性别语音: {other_voices[0].id}"
                print(f"[DEBUG] 备用TTS选择非匹配性别的语音: {other_voices[0].id}")
                self.log(f"警告：系统中没有找到{target_gender}声中文语音，使用了可用的语音")
            
            # 如果没有找到中文语音，使用默认语音
            if not chinese_voice_found:
                print("[DEBUG] 未找到中文语音，使用默认语音")
                self.log("警告：系统中未找到中文语音，使用默认语音")
            
            rate_value = float(self.rate_combo.get().replace('x', '')) if hasattr(self, 'rate_combo') else 1.0
            engine.setProperty('rate', int(150 * rate_value))  # 调整语速
            
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            # 将临时文件移动到最终位置
            if os.path.exists(temp_path):
                shutil.move(temp_path, output_path)
            
            print(f"[DEBUG] 备用TTS生成成功: {output_path}")
            self.log(f"备用TTS配音生成成功 ({selected_voice_info})")
            return output_path
        except Exception as e:
            print(f"[ERROR] 备用TTS生成失败: {type(e).__name__}: {e}")
            return ""
    
    EDGE_TTS_VOICES = {
        "zh-CN-XiaoxiaoNeural": "晓晓（女，温柔）",
        "zh-CN-YunxiNeural": "云希（女，温柔）",
        "zh-CN-XiaoyouNeural": "小优（女，年轻）",
        "zh-CN-YunjianNeural": "云健（男，稳重）",
        "zh-CN-YunhaoNeural": "云浩（男，青春）",
        "zh-CN-XiaochenNeural": "小陈（女，甜美）",
        "zh-CN-XiaohanNeural": "小寒（女，知性）",
        "zh-CN-XiaomengNeural": "小萌（女，活泼）",
        "zh-CN-XiaoningNeural": "小宁（男，磁性）",
    }
    
    FEMALE_VOICES = [
        "zh-CN-XiaoxiaoNeural",
        "zh-CN-YunxiNeural",
        "zh-CN-XiaoyouNeural", 
        "zh-CN-XiaochenNeural",
        "zh-CN-XiaohanNeural",
        "zh-CN-XiaomengNeural"
    ]
    
    MALE_VOICES = [
        "zh-CN-YunjianNeural",
        "zh-CN-YunhaoNeural",
        "zh-CN-XiaoningNeural"
    ]
    
    # 已知可用的语音（经过测试确认）
    WORKING_VOICES = [
        "zh-CN-XiaoxiaoNeural",  # 女声，已测试可用
        "zh-CN-YunxiNeural",     # 注意：当前返回的是男声（服务端问题）
        "zh-CN-YunjianNeural",   # 男声，已测试可用
    ]
    
    def show_audio(self):
        for widget in self.content_frame.winfo_children():
            widget.grid_remove()
        
        row = 0
        
        # 口播配音区域
        audio_frame = ttk.LabelFrame(self.content_frame, text="口播配音", padding="10")
        audio_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(audio_frame, text=f"状态: {'已生成' if self.audio_path else '未生成'}").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # 播放按钮
        self.play_audio_btn = ttk.Button(audio_frame, text="播放", command=self._play_audio, 
                                         state=tk.NORMAL if self.audio_path else tk.DISABLED)
        self.play_audio_btn.grid(row=0, column=1, padx=5)
        
        # 停止按钮
        self.stop_audio_btn = ttk.Button(audio_frame, text="停止", command=self._stop_audio, state=tk.DISABLED)
        self.stop_audio_btn.grid(row=0, column=2, padx=5)
        
        # 重新生成按钮
        self.regenerate_audio_btn = ttk.Button(audio_frame, text="重新生成", command=self._regenerate_audio_only)
        self.regenerate_audio_btn.grid(row=0, column=3, padx=5)
        
        # 播放进度条
        self.audio_progress = ttk.Progressbar(audio_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.audio_progress.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 时间显示
        self.audio_time_label = ttk.Label(audio_frame, text="00:00 / 00:00")
        self.audio_time_label.grid(row=2, column=0, columnspan=4)
        
        # 背景音乐区域
        bgm_frame = ttk.LabelFrame(self.content_frame, text="背景音乐", padding="10")
        bgm_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(bgm_frame, text=f"状态: {'已生成' if self.bgm_path else '未生成'}").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # 播放按钮
        self.play_bgm_btn = ttk.Button(bgm_frame, text="播放", command=self._play_bgm,
                                       state=tk.NORMAL if self.bgm_path else tk.DISABLED)
        self.play_bgm_btn.grid(row=0, column=1, padx=5)
        
        # 停止按钮
        self.stop_bgm_btn = ttk.Button(bgm_frame, text="停止", command=self._stop_bgm, state=tk.DISABLED)
        self.stop_bgm_btn.grid(row=0, column=2, padx=5)
        
        # 播放进度条
        self.bgm_progress = ttk.Progressbar(bgm_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.bgm_progress.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 时间显示
        self.bgm_time_label = ttk.Label(bgm_frame, text="00:00 / 00:00")
        self.bgm_time_label.grid(row=2, column=0, columnspan=4)
        
        # 重新生成按钮
        self.regenerate_bgm_btn = ttk.Button(bgm_frame, text="重新生成背景音乐", command=self._regenerate_bgm_only)
        self.regenerate_bgm_btn.grid(row=0, column=3, padx=5)
        
        # 配音设置区域
        settings_frame = ttk.LabelFrame(self.content_frame, text="配音设置", padding="10")
        settings_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(settings_frame, text="配音音色（Edge-TTS）：").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.voice_combo = ttk.Combobox(settings_frame, values=list(self.EDGE_TTS_VOICES.values()), width=30)
        self.voice_combo.current(0)
        self.voice_combo.grid(row=0, column=1, padx=5)
        
        self.selected_voice = list(self.EDGE_TTS_VOICES.keys())[0]
        
        def on_voice_select(event):
            idx = self.voice_combo.current()
            self.selected_voice = list(self.EDGE_TTS_VOICES.keys())[idx]
        
        self.voice_combo.bind('<<ComboboxSelected>>', on_voice_select)
        
        ttk.Label(settings_frame, text="语速：").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.rate_combo = ttk.Combobox(settings_frame, values=["0.8x", "0.9x", "1.0x", "1.1x", "1.2x", "1.3x"], width=20)
        self.rate_combo.current(2)
        self.rate_combo.grid(row=1, column=1, padx=5)
    
    def _play_audio(self):
        """播放口播配音"""
        if self.audio_path and os.path.exists(self.audio_path):
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(self.audio_path)
                
                # 获取音频时长
                audio_length = pygame.mixer.Sound(self.audio_path).get_length()
                self.audio_progress.config(maximum=audio_length)
                self.audio_length = audio_length
                
                pygame.mixer.music.play()
                
                # 禁用播放按钮，启用停止按钮
                self.play_audio_btn.config(state=tk.DISABLED)
                self.stop_audio_btn.config(state=tk.NORMAL)
                
                # 开始更新进度条
                self._update_audio_progress()
            except Exception as e:
                print(f"播放音频失败: {e}")
                messagebox.showwarning("警告", f"播放音频失败: {e}")
    
    def _play_bgm(self):
        """播放背景音乐"""
        if self.bgm_path and os.path.exists(self.bgm_path):
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(self.bgm_path)
                
                # 获取音频时长
                bgm_length = pygame.mixer.Sound(self.bgm_path).get_length()
                self.bgm_progress.config(maximum=bgm_length)
                self.bgm_length = bgm_length
                
                pygame.mixer.music.play()
                
                # 禁用播放按钮，启用停止按钮
                self.play_bgm_btn.config(state=tk.DISABLED)
                self.stop_bgm_btn.config(state=tk.NORMAL)
                
                # 开始更新进度条
                self._update_bgm_progress()
            except Exception as e:
                print(f"播放背景音乐失败: {e}")
                messagebox.showwarning("警告", f"播放背景音乐失败: {e}")
    
    def _update_audio_progress(self):
        """更新配音播放进度条"""
        try:
            import pygame
            if pygame.mixer.music.get_busy():
                current_pos = pygame.mixer.music.get_pos() / 1000  # 转换为秒
                self.audio_progress.config(value=current_pos)
                
                # 更新时间显示
                current_time = self._format_time(current_pos)
                total_time = self._format_time(self.audio_length)
                self.audio_time_label.config(text=f"{current_time} / {total_time}")
                
                # 继续更新
                self.audio_progress_update = self.root.after(100, self._update_audio_progress)
            else:
                # 播放结束
                self.audio_progress.config(value=self.audio_length)
                self.audio_time_label.config(text=f"{self._format_time(self.audio_length)} / {self._format_time(self.audio_length)}")
                self.play_audio_btn.config(state=tk.NORMAL)
                self.stop_audio_btn.config(state=tk.DISABLED)
        except Exception as e:
            print(f"更新音频进度失败: {e}")
    
    def _update_bgm_progress(self):
        """更新背景音乐播放进度条"""
        try:
            import pygame
            if pygame.mixer.music.get_busy():
                current_pos = pygame.mixer.music.get_pos() / 1000  # 转换为秒
                self.bgm_progress.config(value=current_pos)
                
                # 更新时间显示
                current_time = self._format_time(current_pos)
                total_time = self._format_time(self.bgm_length)
                self.bgm_time_label.config(text=f"{current_time} / {total_time}")
                
                # 继续更新
                self.bgm_progress_update = self.root.after(100, self._update_bgm_progress)
            else:
                # 播放结束
                self.bgm_progress.config(value=self.bgm_length)
                self.bgm_time_label.config(text=f"{self._format_time(self.bgm_length)} / {self._format_time(self.bgm_length)}")
                self.play_bgm_btn.config(state=tk.NORMAL)
                self.stop_bgm_btn.config(state=tk.DISABLED)
        except Exception as e:
            print(f"更新背景音乐进度失败: {e}")
    
    def _format_time(self, seconds):
        """格式化时间显示"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def _stop_audio(self):
        """停止播放口播配音"""
        try:
            import pygame
            pygame.mixer.music.stop()
            
            # 停止进度条更新
            if hasattr(self, 'audio_progress_update'):
                self.root.after_cancel(self.audio_progress_update)
            
            # 重置进度条
            self.audio_progress.config(value=0)
            self.audio_time_label.config(text="00:00 / 00:00")
            
            self.play_audio_btn.config(state=tk.NORMAL)
            self.stop_audio_btn.config(state=tk.DISABLED)
        except Exception as e:
            print(f"停止音频失败: {e}")
    
    def _stop_bgm(self):
        """停止播放背景音乐"""
        try:
            import pygame
            pygame.mixer.music.stop()
            
            # 停止进度条更新
            if hasattr(self, 'bgm_progress_update'):
                self.root.after_cancel(self.bgm_progress_update)
            
            # 重置进度条
            self.bgm_progress.config(value=0)
            self.bgm_time_label.config(text="00:00 / 00:00")
            
            self.play_bgm_btn.config(state=tk.NORMAL)
            self.stop_bgm_btn.config(state=tk.DISABLED)
        except Exception as e:
            print(f"停止背景音乐失败: {e}")
    
    def _regenerate_audio_only(self):
        """仅重新生成口播配音"""
        full_text = self.current_script.get("opening", "") + \
                    self.current_script.get("content", "") + \
                    self.current_script.get("cta", "")
        
        # 更新选中的音色
        if hasattr(self, 'voice_combo'):
            idx = self.voice_combo.current()
            self.selected_voice = list(self.EDGE_TTS_VOICES.keys())[idx]
            print(f"[DEBUG] 使用选中的音色: {self.selected_voice}")
        
        self.log("正在重新生成口播配音...")
        self.audio_path = self._generate_audio_edge_tts(full_text)
        
        if self.audio_path:
            self.log(f"配音生成成功: {self.audio_path}")
            self.play_audio_btn.config(state=tk.NORMAL)
        else:
            self.log("配音生成失败")
        
        self._update_subtitle_timestamps()
    
    def _regenerate_bgm_only(self):
        """仅重新生成背景音乐（异步执行）"""
        self.log("正在重新生成背景音乐...")
        
        # 禁用按钮，显示加载状态
        self.regenerate_bgm_btn.config(state=tk.DISABLED)
        
        # 使用线程异步执行，避免阻塞UI
        import threading
        thread = threading.Thread(target=self._regenerate_bgm_thread, daemon=True)
        thread.start()
    
    def _regenerate_bgm_thread(self):
        """背景音乐重新生成线程"""
        try:
            # 根据口播内容选择情绪
            emotion = self._get_bgm_emotion()
            self.log(f"选择背景音乐情绪: {emotion}")
            
            # 获取口播时长，传递给音乐生成API
            target_duration = 60  # 默认60秒
            if self.audio_path:
                try:
                    import pygame
                    audio_length = pygame.mixer.Sound(self.audio_path).get_length()
                    target_duration = int(audio_length) + 5  # 多5秒缓冲
                    print(f"[DEBUG] 目标背景音乐时长: {target_duration}秒")
                except:
                    pass
            
            # 调用音乐生成API（带超时）
            try:
                import asyncio
                # 设置超时
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                future = asyncio.wait_for(self.minimax.generate_music(emotion, target_duration), timeout=120)
                self.bgm_path = loop.run_until_complete(future)
            except asyncio.TimeoutError:
                self.log("背景音乐生成超时，使用默认音乐")
                self.bgm_path = ""
            
            if self.bgm_path:
                self.log(f"背景音乐生成成功: {self.bgm_path}")
                # 裁剪背景音乐以匹配口播时长
                self._trim_bgm_to_audio_length()
                
                # 更新播放按钮状态
                self.root.after(0, lambda: self.play_bgm_btn.config(state=tk.NORMAL))
            else:
                self.log("背景音乐生成失败")
            
            # 更新UI
            self.root.after(0, self.show_audio)
            
        except Exception as e:
            print(f"[ERROR] 背景音乐生成线程失败: {e}")
            self.log(f"背景音乐生成失败: {str(e)}")
        
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.regenerate_bgm_btn.config(state=tk.NORMAL))
    
    def _get_bgm_emotion(self):
        """根据脚本内容选择背景音乐情绪"""
        script_text = self.current_script.get("opening", "") + \
                      self.current_script.get("content", "") + \
                      self.current_script.get("cta", "")
        
        # 根据内容关键词选择情绪
        keywords = {
            "快乐": ["快乐", "开心", "高兴", "幸福", "喜悦"],
            "温暖": ["温暖", "温馨", "关爱", "陪伴", "成长"],
            "励志": ["励志", "加油", "坚持", "努力", "成功"],
            "轻松": ["轻松", "有趣", "幽默", "简单", "轻松"],
        }
        
        # 默认情绪
        emotion = "warm gentle positive"
        
        # 检测关键词
        for key, words in keywords.items():
            if any(word in script_text for word in words):
                if key == "快乐":
                    emotion = "happy upbeat cheerful"
                elif key == "温暖":
                    emotion = "warm gentle heartfelt"
                elif key == "励志":
                    emotion = "inspirational motivational uplifting"
                elif key == "轻松":
                    emotion = "light playful cheerful"
                break
        
        return emotion
    
    def _trim_bgm_to_audio_length(self):
        """裁剪背景音乐以匹配口播时长"""
        if not self.audio_path or not self.bgm_path:
            return
        
        try:
            import pygame
            import os
            
            # 获取音频时长
            audio_length = pygame.mixer.Sound(self.audio_path).get_length()
            bgm_length = pygame.mixer.Sound(self.bgm_path).get_length()
            
            print(f"[DEBUG] 口播时长: {audio_length:.2f}秒, 背景音乐时长: {bgm_length:.2f}秒")
            
            # 如果背景音乐比口播长，裁剪它
            if bgm_length > audio_length:
                # 使用ffmpeg裁剪
                output_path = "audio/bgm_trimmed.mp3"
                cmd = f'ffmpeg -i "{self.bgm_path}" -t {audio_length:.2f} -c copy "{output_path}"'
                os.system(cmd)
                
                # 替换原文件
                os.remove(self.bgm_path)
                os.rename(output_path, self.bgm_path)
                
                self.log(f"背景音乐已裁剪为 {audio_length:.2f} 秒")
                print(f"[DEBUG] 背景音乐已裁剪为 {audio_length:.2f} 秒")
        except Exception as e:
            print(f"[ERROR] 裁剪背景音乐失败: {e}")
    
    def _generate_subtitles(self):
        if not self.current_script:
            messagebox.showwarning("警告", "请先生成脚本")
            return
        
        self.log("正在调用MiniMax生成字幕...")
        full_text = self.current_script.get("opening", "") + \
                    self.current_script.get("content", "") + \
                    self.current_script.get("cta", "")
        
        prompt = f"""为以下视频脚本生成字幕：
{full_text}

要求：
1. 旁白字幕每句不超过12字，带时间戳（秒）
2. 提取1-2句金句作为重点字幕
3. 直接输出JSON格式，不要有思考过程和额外文字
4. JSON字段：narrator（字幕数组，每元素含text和time字段）、golden（金句数组）

输出格式：
{{
    "narrator": [{{"text": "字幕内容", "time": 0.5}}, ...],
    "golden": ["金句1", "金句2"]
}}"""
        
        result = asyncio.run(self.minimax.chat_completion(prompt))
        
        print("\n" + "="*60)
        print("[DEBUG] 字幕生成结果")
        print(f"[DEBUG] 返回长度: {len(result) if result else 0}")
        print(f"[DEBUG] 返回内容前200字符: {result[:200] if result else '空'}")
        
        try:
            result = result.strip()
            
            if '<think>' in result:
                print("[DEBUG] 移除think标签")
                result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
            
            result = result.strip()
            
            if '```' in result:
                print("[DEBUG] 移除代码块标记")
                parts = result.split('```')
                for part in parts:
                    part = part.strip()
                    if part.startswith('json'):
                        result = part[4:].strip()
                        break
                    elif part.startswith('{'):
                        result = part
                        break
                else:
                    result = parts[-1].strip()
            
            result = result.strip()
            
            if result.startswith('json'):
                print("[DEBUG] 移除json标记")
                result = result[4:].strip()
            
            result = result.strip()
            result = re.sub(r',\s*([}\]])', r'\1', result)
            print("[DEBUG] 处理尾随逗号")
            
            print(f"[DEBUG] 处理后内容前100字符: {result[:100]}")
            
            self.current_subtitles = json.loads(result)
            self.show_subtitles()
            self.log("字幕生成完成")
            self.confirm_btn.config(state=tk.NORMAL)
            self.regenerate_btn.config(state=tk.NORMAL)
            print("[DEBUG] 字幕生成成功")
        except json.JSONDecodeError as e:
            self.log(f"解析字幕失败: {e}")
            print(f"[ERROR] JSON解析失败: {e}")
            print(f"[ERROR] 返回内容: {result[:300]}")
            messagebox.showinfo("提示", "解析字幕失败，已使用默认字幕")
            self._generate_default_subtitles()
        except Exception as e:
            self.log(f"生成字幕失败: {e}")
            messagebox.showinfo("提示", "生成字幕失败，已使用默认字幕")
            print(f"[ERROR] 生成字幕失败: {e}")
            self._generate_default_subtitles()
        
        print("="*60 + "\n")
    
    def _generate_default_subtitles(self):
        full_text = self.current_script.get("opening", "") + \
                    self.current_script.get("content", "") + \
                    self.current_script.get("cta", "")
        
        filtered = re.sub(r'[^\u4e00-\u9fff\w\s？！：]', '', full_text)
        lines = []
        current = ""
        
        for char in filtered:
            current += char
            if len(current) >= 12 or char in '？！：':
                lines.append(current)
                current = ""
        
        if current:
            lines.append(current)
        
        timestamps = []
        time = 0.0
        for line in lines:
            duration = min(len(line) * 0.25 + 0.5, 3.5)
            timestamps.append({"text": line, "start": round(time, 2), "end": round(time + duration, 2)})
            time += duration
        
        self.current_subtitles = {
            "narrator": timestamps,
            "golden": {"text": ["良好的教育", "需要耐心和方法"], "start": 10.0, "end": 14.0}
        }
        
        self.show_subtitles()
        self.confirm_btn.config(state=tk.NORMAL)
        self.regenerate_btn.config(state=tk.NORMAL)
    
    def show_subtitles(self):
        for widget in self.content_frame.winfo_children():
            widget.grid_remove()
        
        ttk.Label(self.content_frame, text="金句字幕：").grid(row=0, column=0, sticky=tk.W)
        golden_frame = ttk.Frame(self.content_frame)
        golden_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        golden_data = self.current_subtitles.get("golden", [])
        # 支持两种格式：列表或字典
        if isinstance(golden_data, dict):
            golden_texts = golden_data.get("text", [])
        elif isinstance(golden_data, list):
            golden_texts = golden_data
        else:
            golden_texts = []
        
        for i, line in enumerate(golden_texts):
            entry = ttk.Entry(golden_frame, width=20)
            entry.insert(0, line)
            entry.grid(row=0, column=i, padx=5)
        
        ttk.Label(self.content_frame, text="旁白字幕（前10条）：").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.subtitle_tree = ttk.Treeview(self.content_frame, columns=('time', 'text'))
        self.subtitle_tree.heading('time', text='时间')
        self.subtitle_tree.heading('text', text='内容')
        
        for sub in self.current_subtitles.get("narrator", [])[:10]:
            time_str = f"{sub['start']:.1f}-{sub['end']:.1f}s"
            self.subtitle_tree.insert('', tk.END, values=(time_str, sub['text']))
        
        self.subtitle_tree.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def _synthesize_video(self):
        debug_info = f"[DEBUG] generated_images count: {len(self.generated_images) if self.generated_images else 0}\n"
        debug_info += f"[DEBUG] audio_path: {self.audio_path}\n"
        debug_info += f"[DEBUG] audio_exists: {os.path.exists(self.audio_path) if self.audio_path else False}\n"
        print(debug_info)
        
        if not self.generated_images:
            messagebox.showwarning("警告", "请先生成图片")
            return
        
        if not self.audio_path:
            messagebox.showwarning("警告", "请先生成音频")
            return
        
        if not os.path.exists(self.audio_path):
            self.log(f"音频文件不存在: {self.audio_path}")
            messagebox.showwarning("警告", "音频文件不存在")
            return
        
        missing_images = [img for img in self.generated_images if not os.path.exists(img)]
        if missing_images:
            self.log(f"缺失图片: {missing_images}")
            messagebox.showwarning("警告", f"部分图片不存在: {missing_images}")
            return
        
        self.log("正在合成视频...")
        
        bgm_path = self.bgm_path if (self.bgm_path and os.path.exists(self.bgm_path)) else ""
        subtitles = self.current_subtitles if hasattr(self, 'current_subtitles') and self.current_subtitles else None
        
        self.log(f"[DEBUG] bgm_path: {bgm_path}")
        self.log(f"[DEBUG] subtitles: {subtitles is not None}")
        
        width = self.selected_resolution.get("width", 720)
        height = self.selected_resolution.get("height", 1280)
        subtitle_scale = self._get_subtitle_scale()
        success = VideoComposer.synthesize(self.generated_images, self.audio_path, bgm_path, subtitles, 
                                           width=width, height=height, subtitle_scale=subtitle_scale,
                                           subtitle_settings=self.subtitle_settings)
        
        if success:
            VideoComposer.generate_cover(self.selected_topic, "让亲子关系更亲密", 
                                         self.generated_images[0] if self.generated_images else "",
                                         width=width, height=height)
            self._generate_delivery_list()
            
            self.log("视频合成完成！")
            self.show_video_result()
            self.confirm_btn.config(state=tk.NORMAL)
            self.preview_btn.config(state=tk.NORMAL)
        else:
            self.log("视频合成失败")
            self.log("请检查FFmpeg是否安装，或查看终端输出的详细错误信息")
            messagebox.showerror("错误", "视频合成失败，请查看日志窗口")
    
    def show_video_result(self):
        for widget in self.content_frame.winfo_children():
            widget.grid_remove()
        
        ttk.Label(self.content_frame, text="视频合成完成！", font=('Arial', 16, 'bold')).grid(row=0, column=0, pady=10)
        
        result_frame = ttk.Frame(self.content_frame)
        result_frame.grid(row=1, column=0)
        
        ttk.Label(result_frame, text="输出文件：").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(result_frame, text="output/final_with_audio.mp4").grid(row=0, column=1)
        
        ttk.Label(result_frame, text="封面图片：").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(result_frame, text="output/cover.png").grid(row=1, column=1)
        
        ttk.Label(result_frame, text="交付清单：").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(result_frame, text="output/delivery清单.json").grid(row=2, column=1)
    
    def _generate_delivery_list(self):
        delivery = {
            "选题": self.selected_topic,
            "脚本": self.current_script,
            "分镜数量": len(self.current_storyboard),
            "分镜摘要": [{k: v for k, v in s.items() if k != 'prompt_en'} for s in self.current_storyboard],
            "字幕示例": self.current_subtitles.get("narrator", [])[:5],
            "金句": self.current_subtitles.get("golden", {}),
            "标题方案": [
                f"三招搞定{self.selected_topic}，让孩子更优秀",
                f"{self.selected_topic}的秘密武器，家长必看",
                f"从困惑到精通，{self.selected_topic}只需这三步"
            ],
            "发布简介": f"你家孩子{self.selected_topic}方面有困扰吗？今天分享三个超实用的{self.selected_topic}技巧，简单易操作，坚持一周就能看到效果。快来试试吧！评论区分享你的经验，我们一起讨论。#亲子教育 #家庭教育 #育儿技巧",
            "标签": ["#亲子教育", "#家庭教育", "#育儿技巧", "#亲子沟通", "#家长课堂"],
            "视频文件": "output/final_with_audio.mp4",
            "封面文件": "output/cover.png",
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("output/delivery清单.json", 'w', encoding='utf-8') as f:
            json.dump(delivery, f, ensure_ascii=False, indent=2)
    
    def confirm_current_step(self):
        if self.current_step == 0:
            selected = self.topic_listbox.curselection()
            if selected:
                self.selected_topic = self.generated_topics[selected[0]]['title']
                self.log(f"选择选题: {self.selected_topic}")
            else:
                messagebox.showwarning("警告", "请选择一个选题")
                return
        
        if self.current_step == 1:
            content = self.script_text.get(1.0, tk.END)
            parts = content.split("【核心干货】")
            if len(parts) >= 2:
                opening = parts[0].replace("【开场钩子】\n", "").strip()
                remaining = parts[1].split("【CTA引导】")
                if len(remaining) >= 2:
                    self.current_script = {
                        "opening": opening,
                        "content": remaining[0].strip(),
                        "cta": remaining[1].strip()
                    }
        
        next_step = self.current_step + 1
        if next_step not in self.completed_steps:
            self.completed_steps.append(next_step)
        
        self._auto_save()  # 自动保存项目
        
        if self.current_step < 5:
            self.current_step = next_step
            self.update_ui()
            self.log(f"进入步骤 {self.current_step+1}")
        
        self.confirm_btn.config(state=tk.DISABLED)
        self.regenerate_btn.config(state=tk.DISABLED)
    
    def regenerate_current_step(self):
        self.regenerate_btn.config(state=tk.DISABLED)
        self.confirm_btn.config(state=tk.DISABLED)
        
        if self.current_step == 0:
            self.topic_listbox.delete(0, tk.END)
        elif self.current_step == 1:
            self.script_text.delete(1.0, tk.END)
        
        self.generate_current_step()
    
    def preview_result(self):
        if os.path.exists("output/final_with_audio.mp4"):
            subprocess.run(["explorer", "output"], shell=True)
        else:
            messagebox.showinfo("提示", "视频文件不存在")

def main():
    root = tk.Tk()
    app = VideoMakerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()