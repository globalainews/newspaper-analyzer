import json
from PIL import Image, ImageDraw

# 这是结构/文本完全不变，但坐标专为 1029 x 2000 尺寸精准标定的 JSON
json_data = """
{
  "newspaper": "The Wall Street Journal",
  "date": "2026-03-14",
  "title": {
    "line1": "WSJ",
    "line2": "THE WALL STREET JOURNAL WEEKEND - SATURDAY/SUNDAY, MARCH 14 - 15, 2026"
  },
  "intro": "今日华尔街日报头版重点报道了美军因中东局势紧张向海湾地区增派兵力的消息，并指出总统在明知风险的情况下仍决定开战。此外，版面还覆盖了美国司法部在美联储调查案中受挫、白宫严控小肯尼迪，以及意大利棒球队文化输出等政经与体育热点。",
  "news_blocks": [
    {
      "id": 1,
      "title": "全球与商业简讯栏 (What's News)",
      "content": "汇总了联邦法官驳回传票、TikTok美国业务交易、五角大楼增兵等全球重点商业与时事简讯。",
      "position": [15, 360, 190, 1980]
    },
    {
      "id": 2,
      "title": "美国向海湾地区增派更多军力",
      "content": "五角大楼向中东派遣额外海军陆战队与军舰，应对紧张局势。",
      "position": [195, 360, 820, 600]
    },
    {
      "id": 3,
      "title": "司法部在鲍威尔调查案中遭受重挫",
      "content": "法官驳回了美联储的传票，称其目的是骚扰，司法部律师将提出上诉。",
      "position": [825, 360, 1015, 1540]
    },
    {
      "id": 4,
      "title": "总统深知封锁霍尔木兹海峡的风险，仍决定开战",
      "content": "配以搜救人员在废墟中救援的巨幅照片，报道总统在听取风险简报后依然下令打击。",
      "position": [195, 600, 820, 1540]
    },
    {
      "id": 5,
      "title": "意大利棒球队凭借浓缩咖啡和阿玛尼接管比赛",
      "content": "意大利裔美国球员在世界棒球经典赛中以对祖国文化的拥抱赢得了球迷喜爱。",
      "position": [195, 1540, 505, 1980]
    },
    {
      "id": 6,
      "title": "400亿美元产业的交流",
      "content": "聚焦青年体育产业的商业发展与影响的图文预告板块。",
      "position": [510, 1540, 665, 1980]
    },
    {
      "id": 7,
      "title": "白宫对小罗伯特·肯尼迪严加看管",
      "content": "白宫加强了对卫生与公众服务部信息传播和政策的控制，以防范失误。",
      "position": [670, 1540, 1015, 1980]
    }
  ],
  "main_content_area": [15, 360, 1015, 1980]
}
"""

def draw_preview_boxes(image_path, output_path="preview_result_1029x2000.jpg"):
    # 1. 解析 JSON 数据
    data = json.loads(json_data)

    # 2. 打开原始图片
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        print(f"错误: 找不到图片 '{image_path}'。请确保路径正确。")
        return

    # 3. 【核心步骤】强制将图片尺寸调整为您指定的 1029 x 2000
    # 这样可以确保新计算的坐标 100% 贴合画面内容
    img = img.resize((1029, 2000), Image.Resampling.LANCZOS)
    
    # 创建绘图对象
    draw = ImageDraw.Draw(img)

    # 4. 绘制整体内容区域 (Main Area，使用红色虚线或粗线)
    main_area = data.get("main_content_area")
    if main_area:
        draw.rectangle(main_area, outline="red", width=4)
        draw.text((main_area[0] + 5, main_area[1] + 5), "Main Area", fill="red")

    # 5. 循环绘制每一条新闻的区块 (使用蓝色线)
    for block in data.get("news_blocks", []):
        pos = block["position"]
        block_id = block["id"]
        
        # 绘制蓝色矩形边框
        draw.rectangle(pos, outline="blue", width=4)
        
        # 绘制左上角的 ID 标签背景和文字
        label_bg = [pos[0], pos[1], pos[0] + 25, pos[1] + 25]
        draw.rectangle(label_bg, fill="blue")
        draw.text((pos[0] + 8, pos[1] + 5), str(block_id), fill="white")

    # 6. 保存并显示结果图片
    img.save(output_path)
    print(f"✅ 绘制完成！尺寸已调整为 1029x2000，预览图已保存为: {output_path}")
    
    # 自动打开图片
    img.show()

if __name__ == "__main__":
    # 请将此处替换为您实际存放的附件图片的文件名
    SOURCE_IMAGE = "newspaper.jpg"  
    draw_preview_boxes(SOURCE_IMAGE)