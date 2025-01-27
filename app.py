import threading

from flask import Flask, render_template, request, send_from_directory, jsonify
import asyncio
import edge_tts
import os
from datetime import datetime
import uuid
import webbrowser

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'audio'

# 确保音频目录存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 定义角色映射
VOICE_MAP = {
    "云溪（男）": "zh-CN-YunxiNeural",
    "晓晓（女）": "zh-CN-XiaoxiaoNeural",
    "云野（男）": "zh-CN-YunyangNeural",
    "晓晨（女）": "zh-CN-XiaochenNeural",
    # 可以根据需要添加更多角色
    "云阳（男）": "zh-CN-YunyangNeural"

}


async def text_to_speech(text, output_file, voice="zh-CN-YunxiNeural", rate="+0%", pitch="+0Hz", volume="+0%"):
    communicate = edge_tts.Communicate(
        text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume
    )
    await communicate.save(output_file)


def generate_unique_filename(folder):
    """
    生成唯一的文件名
    :param folder: 文件夹路径
    :return: 唯一的文件名
    """
    while True:
        # 生成随机文件名
        filename = str(uuid.uuid4()) + ".mp3"
        filepath = os.path.join(folder, filename)
        # 检查文件是否已存在
        if not os.path.exists(filepath):
            return filename


def convert_percentage_to_value(percentage, param_type):
    """
    将百分比值转换为 edge_tts 所需的格式
    :param percentage: 百分比值 (0-100)
    :param param_type: 参数类型 ('rate', 'pitch', 'volume')
    :return: 转换后的值
    """
    percentage = int(percentage)
    if param_type == 'rate':
        # 语速：0-100 转换为 -50% 到 +50%
        value = percentage - 50
        return f"{'+' if value >= 0 else ''}{value}%"
    elif param_type == 'pitch':
        # 音高：0-100 转换为 -50Hz 到 +50Hz
        value = percentage - 50
        return f"{'+' if value >= 0 else ''}{value}Hz"
    elif param_type == 'volume':
        # 音量：0-100 转换为 -50% 到 +50%
        value = percentage - 50
        return f"{'+' if value >= 0 else ''}{value}%"
    else:
        raise ValueError("Invalid parameter type")


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', voices=VOICE_MAP.keys())


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    text = data.get('text')
    rate = convert_percentage_to_value(data.get('rate', '50'), 'rate')
    pitch = convert_percentage_to_value(data.get('pitch', '50'), 'pitch')
    volume = convert_percentage_to_value(data.get('volume', '50'), 'volume')
    voice_name = data.get('voice', '云溪（男）')
    voice = VOICE_MAP.get(voice_name, "zh-CN-YunxiNeural")  # 默认使用云溪

    # 获取当前日期，格式为 YYYY-MM-DD
    today = datetime.now().strftime('%Y-%m-%d')
    # 创建以日期命名的文件夹
    date_folder = os.path.join(app.config['UPLOAD_FOLDER'], today)
    if not os.path.exists(date_folder):
        os.makedirs(date_folder)

    # 生成唯一的文件名
    filename = generate_unique_filename(date_folder)
    output_file = os.path.join(date_folder, filename)

    # 运行异步函数
    asyncio.run(text_to_speech(text, output_file, voice, rate, pitch, volume))

    # 返回音频文件的相对路径（相对于 UPLOAD_FOLDER）
    return jsonify({
        'audio_file': os.path.join(today, filename)
    })


@app.route('/audio/<path:filename>')
def audio(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def open_browser():
    webbrowser.open('http://127.0.0.1:8999/')

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()  # 延迟 1 秒后打开浏览器 放在前面 在主线程阻塞之前开辟一个新线程处理逻辑
    app.run(debug=False,port=8999,use_reloader=False) # 这行代码要放在后面 因为运行之后会阻塞主线程


