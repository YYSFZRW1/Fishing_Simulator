import random
import time
import sys
import msvcrt
import re
import json
import os

# 鱼的种类和名称
FISH_TYPES = {
    "Common": ["鲤鱼", "鲈鱼", "鲫鱼", "鳕鱼", "罗非鱼", "鲶鱼", "草鱼", "鲢鱼", "黄花鱼", "带鱼"],
    "Rare": ["鲑鱼", "金枪鱼", "比目鱼", "石斑鱼", "鲷鱼", "鳗鱼", "鲟鱼", "三文鱼", "沙丁鱼", "鳟鱼"],
    "Legendary": ["龙鱼", "深海巨怪", "幻彩鱼", "蓝鳍金枪鱼", "帝王鲑", "大白鲨", "翻车鱼", "皇带鱼", "神仙鱼", "魟鱼"],
    "Epic": ["yeyu", "moyu"]
}

# 鱼竿配置
ROD_TYPES = {
    "Common": {"name": "普通鱼竿", "time_bonus": 1.0, "factor_bonus": 1.0},
    "Rare": {"name": "精良鱼竿", "time_bonus": 1.1, "factor_bonus": 0.9},
    "Epic": {"name": "史诗鱼竿", "time_bonus": 1.2, "factor_bonus": 0.8},
    "Legendary": {"name": "传说鱼竿", "time_bonus": 1.3, "factor_bonus": 0.7}
}

# 鱼竿掉落概率
DROP_PROBS = {
    "Common": {"Common": 0.05},
    "Rare": {"Rare": 0.05},
    "Legendary": {"Epic": 0.05}
}

# 鱼价格（金币/千克）
FISH_PRICES = {
    "Common": 1,
    "Rare": 3,
    "Legendary": 10,
    "Epic": 20
}

# 鱼竿价格（普通鱼 1千克 × 20 倍 × 5）
ROD_PRICES = {
    "Common": 100,
    "Rare": 300,
    "Epic": 1000,
    "Legendary": 2000
}

# 嘲讽信息
MOCKING_MESSAGES = {
    "Common": ["哈哈，太慢了！", "你这水平还想抓我？", "再练几年吧，人类！"],
    "Rare": ["我游得比你快多了！", "下次再来试试吧，弱者！"],
    "Legendary": ["你连我的鳞片都摸不到！", "鱼中之王岂是你能抓的？"],
    "Epic": ["摸鱼失败，回家睡觉吧！", "yeyu/moyu 岂是你能驾驭的？", "连鱼都比你勤奋！"]
}

# 难度配置
DIFFICULTY_CONFIG = {
    1: {"name": "简单", "time_base": 13.2, "time_factor": 0.3, "weight_range": (0.5, 3.0),
        "type_probs": (0.80, 0.15, 0.05, 0.0)},
    2: {"name": "中等", "time_base": 11.0, "time_factor": 0.5, "weight_range": (1.0, 6.0),
        "type_probs": (0.50, 0.30, 0.20, 0.0)},
    3: {"name": "高级", "time_base": 8.8, "time_factor": 0.7, "weight_range": (2.0, 10.0),
        "type_probs": (0.20, 0.40, 0.40, 0.0)},
    4: {"name": "你抓不到我", "time_base": 5.5, "time_factor": 0.9, "weight_range": (5.0, 15.0),
        "type_probs": (0.05, 0.15, 0.80, 0.0)},
    5: {"name": "unbelievable", "time_base": 4.5, "time_factor": 1.0, "weight_range": (8.0, 20.0),
        "type_probs": (0.05, 0.15, 0.30, 0.50)}
}

# 成就配置
ACHIEVEMENTS = {
    "cast_10": {"name": "新手渔夫", "condition": lambda stats: stats["cast_count"] >= 10, "unlocked": False},
    "cast_30": {"name": "熟练渔夫", "condition": lambda stats: stats["cast_count"] >= 30, "unlocked": False},
    "cast_100": {"name": "钓鱼大师", "condition": lambda stats: stats["cast_count"] >= 100, "unlocked": False},
    "full_collection": {"name": "鱼类收藏家", "condition": lambda stats: len(
        stats["caught_fish_types"] & set(sum([FISH_TYPES[t] for t in ["Common", "Rare", "Legendary"]], []))) == 30,
                        "unlocked": False}
}


# 保存游戏数据
def save_game(inventory, rods, equipped_rod, gold, stats, difficulty, difficulty_unlocked):
    data = {
        "inventory": inventory,
        "rods": rods,
        "equipped_rod": {"type": [k for k, v in ROD_TYPES.items() if v == equipped_rod][0]},
        "gold": gold,
        "stats": {"cast_count": stats["cast_count"], "caught_fish_types": list(stats["caught_fish_types"])},
        "achievements": {k: {"name": v["name"], "unlocked": v["unlocked"]} for k, v in ACHIEVEMENTS.items()},
        "difficulty": difficulty,
        "difficulty_unlocked": difficulty_unlocked
    }
    save_path = os.path.join("dist", "save_data.json")
    os.makedirs("dist", exist_ok=True)  # 确保 dist 目录存在
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("游戏进度已保存")
    except Exception as e:
        print(f"保存失败：{e}")


# 加载游戏数据
def load_game():
    save_path = os.path.join("dist", "save_data.json")
    if not os.path.exists(save_path):
        print("未找到存档，初始化新游戏")
        return [], [{"type": "Common", "name": ROD_TYPES["Common"]["name"]}], ROD_TYPES["Common"], 0, {"cast_count": 0,
                                                                                                       "caught_fish_types": set()}, 1, False

    try:
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        inventory = data.get("inventory", [])
        rods = data.get("rods", [{"type": "Common", "name": ROD_TYPES["Common"]["name"]}])
        equipped_rod = ROD_TYPES.get(data.get("equipped_rod", {}).get("type", "Common"), ROD_TYPES["Common"])
        gold = data.get("gold", 0)
        stats = {
            "cast_count": data.get("stats", {}).get("cast_count", 0),
            "caught_fish_types": set(data.get("stats", {}).get("caught_fish_types", []))
        }
        for key, ach in data.get("achievements", {}).items():
            if key in ACHIEVEMENTS:
                ACHIEVEMENTS[key]["unlocked"] = ach["unlocked"]
        difficulty = data.get("difficulty", 1)
        difficulty_unlocked = data.get("difficulty_unlocked", False)
        print("已加载存档")
        return inventory, rods, equipped_rod, gold, stats, difficulty, difficulty_unlocked
    except Exception as e:
        print(f"加载存档失败：{e}，初始化新游戏")
        return [], [{"type": "Common", "name": ROD_TYPES["Common"]["name"]}], ROD_TYPES["Common"], 0, {"cast_count": 0,
                                                                                                       "caught_fish_types": set()}, 1, False


# 清空键盘缓冲区
def clear_keyboard_buffer():
    while msvcrt.kbhit():
        msvcrt.getch()


# 随机生成一条鱼
def generate_fish(difficulty):
    config = DIFFICULTY_CONFIG[difficulty]
    r = random.random()
    if r < config["type_probs"][0]:
        fish_type = "Common"
    elif r < sum(config["type_probs"][:2]):
        fish_type = "Rare"
    elif r < sum(config["type_probs"][:3]):
        fish_type = "Legendary"
    else:
        fish_type = "Epic"
    name = random.choice(FISH_TYPES[fish_type])
    weight = round(random.uniform(*config["weight_range"]), 2)
    return {"name": name, "type": fish_type, "weight": weight}


# 生成WASD序列
def generate_wasd_sequence(fish, difficulty, rod):
    fish_type = fish["type"]
    if fish_type == "Common":
        length = random.randint(4, 6)
    elif fish_type == "Rare":
        length = random.randint(6, 8)
    elif fish_type == "Legendary":
        length = random.randint(8, 10)
    else:
        length = random.randint(10, 12)  # Epic 鱼更长序列
    sequence = [random.choice(['W', 'A', 'S', 'D']) for _ in range(length)]
    config = DIFFICULTY_CONFIG[difficulty]
    time_limit = max(3.0, (config["time_base"] * rod["time_bonus"]) - fish["weight"] * (
                config["time_factor"] * rod["factor_bonus"]))
    return sequence, time_limit


# 非阻塞输入
def get_input_with_timeout(timeout):
    start_time = time.time()
    user_input = []
    clear_keyboard_buffer()
    while time.time() - start_time < timeout:
        if msvcrt.kbhit():
            try:
                char = msvcrt.getch().decode('utf-8').upper()
                if char in ['W', 'A', 'S', 'D']:
                    user_input.append(char)
                    print(f"输入: {char}")
                else:
                    print(f"忽略无效输入: {char}")
            except UnicodeDecodeError:
                pass
        time.sleep(0.001)
    return user_input


# 钓鱼挑战
def fishing_challenge(fish, difficulty, rod, stats):
    config = DIFFICULTY_CONFIG[difficulty]
    print(f"\n一条 {fish['type']} 的 {fish['name']} 上钩了！重量: {fish['weight']} 千克")
    sequence, time_limit = generate_wasd_sequence(fish, difficulty, rod)
    print(f"请在 {time_limit:.1f} 秒内按顺序输入以下按键（支持 W/w, A/a, S/s, D/d，仅限单字符输入）: {' '.join(sequence)}")

    user_input = get_input_with_timeout(time_limit)

    if user_input == sequence:
        print(f"成功捕获 {fish['name']}！")
        if fish["name"] == "yeyu":
            print("yeyu被钓走了QAQ")
        elif fish["name"] == "moyu":
            print("上班不准摸鱼 哼！！！")
        return True, None
    else:
        print(f"输入错误或超时，{fish['name']} 逃跑了！")
        print(f"预期输入: {' '.join(sequence)}")
        print(f"你的输入: {' '.join(user_input) if user_input else '无'}")
        if difficulty >= 4:
            print(random.choice(MOCKING_MESSAGES[fish["type"]]))
        # 鱼竿掉落
        if fish["type"] in DROP_PROBS and random.random() < 0.05:
            rod_type = random.choice(list(DROP_PROBS[fish["type"]].keys()))
            print(f"你发现了一根{ROD_TYPES[rod_type]['name']}！")
            return False, rod_type
        return False, None


# 商店界面
def shop_menu(gold, rods):
    print(f"\n=== 商店 ===")
    print(f"当前金币: {gold}")
    print("可购买鱼竿：")
    for i, rod_type in enumerate(ROD_TYPES.keys(), 1):
        print(f"{i}. {ROD_TYPES[rod_type]['name']} - {ROD_PRICES[rod_type]} 金币")
    print("输入 'buy <编号>' 购买鱼竿，或 'back' 返回")

    while True:
        clear_keyboard_buffer()
        command = input("\n商店命令: ").strip().lower()
        command = re.sub(r'[^a-z0-9\s]', '', command)
        if command == "back":
            return gold, None
        if command.startswith("buy "):
            try:
                rod_num = int(command.split()[1])
                if 1 <= rod_num <= len(ROD_TYPES):
                    rod_type = list(ROD_TYPES.keys())[rod_num - 1]
                    if gold >= ROD_PRICES[rod_type]:
                        print(f"成功购买 {ROD_TYPES[rod_type]['name']}！")
                        return gold - ROD_PRICES[rod_type], rod_type
                    else:
                        print("金币不足！")
                else:
                    print("无效鱼竿编号！")
            except (IndexError, ValueError):
                print("请输入 'buy <编号>'（如 buy 1）")
        else:
            print("无效命令！请输入 'buy <编号>' 或 'back'")


# 成就检查
def check_achievements(stats, difficulty_unlocked):
    unlocked = False
    for key, ach in ACHIEVEMENTS.items():
        if not ach["unlocked"] and ach["condition"](stats):
            ach["unlocked"] = True
            print(f"\n成就解锁：{ach['name']}！")
            unlocked = True
    if not difficulty_unlocked and ACHIEVEMENTS["full_collection"]["unlocked"]:
        print("新难度解锁：unbelievable！使用 'difficulty 5' 进入")
        return True
    return difficulty_unlocked or unlocked


# 炫耀功能
def brag_inventory(inventory):
    if not inventory:
        print("背包为空，无法炫耀！")
    else:
        print("\n看我钓的鱼多厉害！🐟")
        for i, fish in enumerate(inventory, 1):
            print(f"{i}. [{fish['type']}] {fish['name']} - {fish['weight']} 千克")


# 帮助命令
def show_help(difficulty_unlocked):
    print("\n=== 命令帮助 ===")
    print("所有命令支持任意大小写（如 CAST, cast），可忽略空格")
    print("可用命令：")
    print("  cast              - 抛竿开始钓鱼")
    print("  inventory         - 查看已捕获的鱼及其价值")
    print("  rods              - 查看拥有的鱼竿")
    print("  equip <编号>      - 装备指定鱼竿（如 equip 1）")
    print("  shop              - 进入商店，查看/购买鱼竿")
    print("  sell <编号>       - 出售背包中的鱼（如 sell 1）")
    print("  difficulty <1-4>  - 切换难度（1：简单，2：中等，3：高级，4：你抓不到我）")
    if difficulty_unlocked:
        print("  difficulty 5      - 切换到 unbelievable 难度")
    else:
        print("  difficulty 5      - unbelievable 难度（未解锁，需全图鉴）")
    print("  achievements      - 查看已解锁的成就")
    print("  brag              - 炫耀背包中的鱼")
    print("  help              - 显示此帮助信息")
    print("  exit              - 退出游戏")


# 主游戏循环
def main():
    print("欢迎体验命令行钓鱼模拟器！")
    print("请选择难度: 1（简单）, 2（中等）, 3（高级）, 4（你抓不到我）, 5（unbelievable，未解锁）")

    # 加载存档
    inventory, rods, equipped_rod, gold, stats, difficulty, difficulty_unlocked = load_game()

    # 验证难度（防止加载无效难度）
    if difficulty not in DIFFICULTY_CONFIG or (difficulty == 5 and not difficulty_unlocked):
        difficulty = 1
        print(f"无效存档难度，已重置为：{DIFFICULTY_CONFIG[difficulty]['name']}")

    print(f"已选择难度: {DIFFICULTY_CONFIG[difficulty]['name']}")
    print("命令: cast, inventory, rods, equip, shop, sell, difficulty, achievements, brag, help, exit（支持任意大小写）")

    while True:
        print(f"\n当前金币: {gold} | 装备鱼竿: {equipped_rod['name']} | 难度: {DIFFICULTY_CONFIG[difficulty]['name']}")
        clear_keyboard_buffer()
        raw_command = input("请输入命令: ").strip()
        command = re.sub(r'[^a-z0-9\s]', '', raw_command).lower()

        if command == "cast":
            stats["cast_count"] += 1
            print("抛竿中...")
            time.sleep(random.uniform(1, 3))
            fish = generate_fish(difficulty)
            success, new_rod = fishing_challenge(fish, difficulty, equipped_rod, stats)
            if success:
                inventory.append(fish)
                stats["caught_fish_types"].add(fish["name"])
            elif new_rod:
                rods.append({"type": new_rod, "name": ROD_TYPES[new_rod]["name"]})
            difficulty_unlocked = check_achievements(stats, difficulty_unlocked)
            save_game(inventory, rods, equipped_rod, gold, stats, difficulty, difficulty_unlocked)
        elif command == "inventory":
            if not inventory:
                print("背包为空！")
            else:
                print("\n已捕获的鱼:")
                for i, fish in enumerate(inventory, 1):
                    price = int(fish["weight"] * FISH_PRICES[fish["type"]])
                    print(f"{i}. {fish['type']} - {fish['name']} ({fish['weight']} 千克，价值 {price} 金币)")
        elif command == "rods":
            if len(rods) == 1 and rods[0]["type"] == "Common":
                print("鱼竿背包: 仅拥有默认普通鱼竿")
            else:
                print("\n鱼竿背包:")
                for i, rod in enumerate(rods, 1):
                    print(f"{i}. {rod['name']}{'（装备中）' if rod['name'] == equipped_rod['name'] else ''}")
        elif command.startswith("equip "):
            try:
                rod_num = int(command.split()[1])
                if 1 <= rod_num <= len(rods):
                    equipped_rod = ROD_TYPES[rods[rod_num - 1]["type"]]
                    print(f"已装备 {equipped_rod['name']}")
                    save_game(inventory, rods, equipped_rod, gold, stats, difficulty, difficulty_unlocked)
                else:
                    print("无效鱼竿编号！")
            except (IndexError, ValueError):
                print("请输入 'equip <编号>'（如 equip 1）")
        elif command == "shop":
            gold, new_rod = shop_menu(gold, rods)
            if new_rod:
                rods.append({"type": new_rod, "name": ROD_TYPES[new_rod]["name"]})
                save_game(inventory, rods, equipped_rod, gold, stats, difficulty, difficulty_unlocked)
        elif command.startswith("sell "):
            try:
                fish_num = int(command.split()[1])
                if 1 <= fish_num <= len(inventory):
                    fish = inventory.pop(fish_num - 1)
                    price = int(fish["weight"] * FISH_PRICES[fish["type"]])
                    gold += price
                    print(f"已出售 {fish['type']} - {fish['name']}，获得 {price} 金币")
                    save_game(inventory, rods, equipped_rod, gold, stats, difficulty, difficulty_unlocked)
                else:
                    print("无效鱼编号！")
            except (IndexError, ValueError):
                print("请输入 'sell <编号>'（如 sell 1）")
        elif command.startswith("difficulty "):
            try:
                new_difficulty = int(command.split()[1])
                if new_difficulty in DIFFICULTY_CONFIG and (new_difficulty != 5 or difficulty_unlocked):
                    difficulty = new_difficulty
                    print(f"已切换难度: {DIFFICULTY_CONFIG[difficulty]['name']}")
                    save_game(inventory, rods, equipped_rod, gold, stats, difficulty, difficulty_unlocked)
                else:
                    print("请输入1到4之间的数字！（unbelievable 需全图鉴解锁）")
            except (IndexError, ValueError):
                print("请输入 'difficulty <1-5>'（如 difficulty 3）")
        elif command == "achievements":
            print("\n=== 成就 ===")
            any_unlocked = False
            for key, ach in ACHIEVEMENTS.items():
                status = "已解锁" if ach["unlocked"] else "未解锁"
                print(f"{ach['name']} - {status}")
                if ach["unlocked"]:
                    any_unlocked = True
            if not any_unlocked:
                print("暂无解锁的成就，继续钓鱼吧！")
        elif command == "brag":
            brag_inventory(inventory)
        elif command == "help":
            show_help(difficulty_unlocked)
        elif command == "exit":
            save_game(inventory, rods, equipped_rod, gold, stats, difficulty, difficulty_unlocked)
            print("感谢游玩，再见！")
            break
        else:
            print(
                f"无效命令: '{raw_command}'！请使用 cast, inventory, rods, equip, shop, sell, difficulty, achievements, brag, help 或 exit（支持任意大小写）。")
            if any(c.upper() in ['W', 'A', 'S', 'D'] for c in raw_command):
                print("提示：捕鱼时请在鱼上钩后输入 W/w, A/a, S/s, D/d，不要在命令中输入这些字符。")


if __name__ == "__main__":
    main()