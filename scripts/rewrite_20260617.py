#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rewrite step for 2026-06-17 daily report.
Updates headline, context, thread_text, threads_text, voice_text,
confidence, opinion_level, claim_trace for 17 selected events.
"""

import json
import os

EVENTS_DIR = "/home/user/akasha-rss-news/data/events/2026-06-17"

REWRITES = {

    # ── INTL ──────────────────────────────────────────────────────────────

    "daily_20260617_evt_284": {
        "headline": "俄艦英吉利海峽鳴槍示警",
        "context": (
            "俄羅斯護衛艦阿德米拉爾・格里戈羅維奇號近日在英吉利海峽活動，"
            "一艘帆船漂近時，艦方開槍示警以防碰撞。"
            "英國政府已就此事展開調查。"
        ),
        "thread_text": (
            "俄艦英吉利海峽鳴槍示警\n\n"
            "俄羅斯護衛艦阿德米拉爾・格里戈羅維奇號近期在英吉利海峽執行任務。"
            "一艘帆船漂向該艦，艦方為避免碰撞，發射警告彈。"
            "英國政府已宣布就此事件展開調查。\n\n"
            "—— 本則整理自 Reuters、BBC 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "俄艦英吉利海峽鳴槍示警\n\n"
            "俄羅斯護衛艦阿德米拉爾・格里戈羅維奇號近期在英吉利海峽執行任務。"
            "一艘帆船漂向該艦，艦方為避免碰撞，向外發射警告彈。"
            "事件發生後，英國政府已宣布展開正式調查，確認具體經過。\n\n"
            "—— 本則整理自 Reuters、BBC 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "俄羅斯軍艦在英吉利海峽鳴槍了。"
            "一艘帆船漂向正在海峽執行任務的護衛艦，"
            "艦方開槍示警，避免發生碰撞。"
            "目前英國政府已介入調查，想弄清楚當時究竟發生了什麼事。"
        ),
        "confidence": "high",
        "opinion_level": "none",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "俄羅斯護衛艦阿德米拉爾・格里戈羅維奇號在英吉利海峽對漂近的帆船鳴槍示警",
                "source_id": "reuters_world_google_news",
                "source_title": "Russian frigate fires warning shots near UK waters to avert yacht collision - Reuters",
                "source_url": "https://news.google.com/rss/articles/CBMixgFBVV95cUxPSVpXOVJQeHJXOTUyeXlSRmE4RGNGRkJ5cHlVXzNyQjM2aktxRTJ0Q1p0cGl1cHIyem1jSEIyajY2YnRNOXBaNkJjZDMtWUlnZG80YU1YTGZDT1NTczcxUGt2V2V5OHNkRkFGLUE5Q1B3b18xdE9scmdvNXl5bXEtRVJHcUpPdnp2eUFEc1lzMjZUeHIzY3puLVlNOGJqRVc5dG9nZmtocUNPWUlNTW5sQlBkZFU0UnFyRmw0UXNhT0h6VHZ6M0E?oc=5",
                "support_type": "direct"
            },
            {
                "claim": "帆船漂向該護衛艦，英國政府展開調查",
                "source_id": "bbc_world",
                "source_title": "UK investigating reports Russian warship fired warning shots near yacht in English Channel",
                "source_url": "https://www.bbc.com/news/articles/c20yzm84r7lo?at_medium=RSS&at_campaign=rss",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_214": {
        "headline": "FBI 破獲白宮攻擊陰謀",
        "context": (
            "FBI 破獲一起針對白宮 UFC 活動的攻擊計畫，"
            "23 人涉案，其中 5 人已遭逮捕，"
            "嫌犯原計畫使用狙擊手與無人機發動攻擊，"
            "動機涉及對政府腐敗、艾普斯坦文件及數據中心政策的不滿。"
        ),
        "thread_text": (
            "FBI 破獲白宮攻擊陰謀\n\n"
            "FBI 成功阻止一起針對白宮 UFC 活動的攻擊計畫。"
            "涉案共 23 人，目前已有 5 人被捕。"
            "嫌犯計畫動用狙擊手與無人機。"
            "調查顯示，該團體對政府腐敗、艾普斯坦文件及數據中心政策抱有不滿。\n\n"
            "—— 本則整理自 Al Jazeera、BBC 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "FBI 破獲白宮攻擊陰謀\n\n"
            "FBI 成功阻止一起針對白宮 UFC 活動的攻擊計畫。"
            "23 人涉及此案，目前已有 5 人被逮捕。"
            "嫌犯原計畫動用狙擊手與無人機發動攻擊。"
            "調查顯示，該團體對政府腐敗問題、艾普斯坦文件解密及數據中心相關政策深感不滿，"
            "以此作為行動動機。\n\n"
            "—— 本則整理自 Al Jazeera、BBC 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "FBI 剛破獲一起針對白宮活動的攻擊計畫。"
            "23 個人涉案，已有 5 人被捕。"
            "他們打算用狙擊手和無人機。"
            "這個團體對腐敗、艾普斯坦文件還有數據中心政策都有強烈不滿。"
        ),
        "confidence": "high",
        "opinion_level": "none",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "FBI 破獲針對白宮 UFC 活動的攻擊計畫，23 人涉案、5 人被捕",
                "source_id": "aljazeera_world",
                "source_title": "FBI foils plot targeting White House UFC event",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "嫌犯計畫使用狙擊手與無人機，動機涉及腐敗、艾普斯坦文件及數據中心",
                "source_id": "bbc_world",
                "source_title": "FBI foils plot targeting White House UFC event with snipers and drones",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_243": {
        "headline": "以色列奪管希伯崙聖地",
        "context": (
            "以色列接管了西岸城市希伯崙一處爭議聖地的行政管理權，"
            "此前該地由巴勒斯坦方面管轄。"
            "希伯崙市長警告此舉違反既有協議，"
            "並可能對區域穩定帶來重大衝擊。"
        ),
        "thread_text": (
            "以色列奪管希伯崙聖地\n\n"
            "以色列宣布接管西岸希伯崙一處具高度爭議性的聖地行政管理權，"
            "此前由巴勒斯坦管轄。"
            "希伯崙市長發出警告，指此舉違反現行協議，"
            "並可能為區域穩定帶來嚴重後果。\n\n"
            "—— 本則整理自 Reuters、Al Jazeera 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "以色列奪管希伯崙聖地\n\n"
            "以色列宣布接管西岸希伯崙一處具高度爭議性的聖地行政管理權，"
            "該地此前一直由巴勒斯坦方面管轄。"
            "希伯崙市長對此強烈警告，指以色列的舉動違反了既有協議框架，"
            "並可能對區域穩定造成「重大後果」。\n\n"
            "—— 本則整理自 Reuters、Al Jazeera 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "以色列接管了西岸希伯崙的一處聖地。"
            "這個地點原本由巴勒斯坦管轄，現在換手了。"
            "希伯崙市長說，這違反了雙方的協議，"
            "可能讓本來就脆弱的區域局勢更加不穩定。"
        ),
        "confidence": "high",
        "opinion_level": "none",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "以色列取得希伯崙爭議聖地的行政管理權",
                "source_id": "reuters_world_google_news",
                "source_title": "Israel seizes administrative control of West Bank shrine from Palestinians",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "希伯崙市長警告此舉違反協議，對區域穩定有重大後果",
                "source_id": "aljazeera_world",
                "source_title": "Israel seizes control of flashpoint shrine in Hebron",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_257": {
        "headline": "以軍無人機攻黎南四人死",
        "context": (
            "以色列軍方無人機在黎巴嫩南部城市納巴提耶攻擊多輛車輛，"
            "造成至少 4 人死亡。"
            "事件發生於伊朗與美國之間停火談判的敏感時期。"
        ),
        "thread_text": (
            "以軍無人機攻黎南四人死\n\n"
            "以色列軍方無人機在黎巴嫩南部納巴提耶對多輛車輛發動攻擊，"
            "造成至少 4 人死亡。"
            "事件發生時，伊朗與美國的停火談判正處於脆弱關鍵階段。\n\n"
            "—— 本則整理自 Reuters、Al Jazeera 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "以軍無人機攻黎南四人死\n\n"
            "以色列軍方無人機在黎巴嫩南部城市納巴提耶發動攻擊，鎖定多輛車輛，"
            "造成至少 4 人死亡。"
            "此次攻擊發生於伊朗與美國停火談判持續進行、局勢仍相當脆弱的時間點，"
            "引發外界對後續走向的高度關注。\n\n"
            "—— 本則整理自 Reuters、Al Jazeera 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "黎巴嫩南部今天又傳出攻擊事件。"
            "無人機在納巴提耶打了幾輛車，至少 4 人罹難。"
            "時間點很微妙——就在伊朗和美國的停火談判進行中，"
            "這樣的衝突讓整個談判格外脆弱。"
        ),
        "confidence": "high",
        "opinion_level": "none",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "以色列無人機在黎巴嫩納巴提耶攻擊車輛，至少 4 人死亡",
                "source_id": "reuters_world_google_news",
                "source_title": "Israeli drone strikes kill 4 in southern Lebanon",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "攻擊發生於伊朗與美國停火談判進行期間",
                "source_id": "aljazeera_world",
                "source_title": "Israeli drone strikes kill 4 amid fragile Iran-US ceasefire talks",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_264": {
        "headline": "批普亭俄藝術家波蘭遇刺",
        "context": (
            "俄羅斯藝術家羅伯特・庫佐夫科夫，筆名謝苗・斯克列佩茨基，"
            "以繪製包括普亭在內的政治人物諷刺漫畫著稱。"
            "他在波蘭遭到槍殺身亡。"
        ),
        "thread_text": (
            "批普亭俄藝術家波蘭遇刺\n\n"
            "俄羅斯藝術家羅伯特・庫佐夫科夫（筆名謝苗・斯克列佩茨基）在波蘭遭槍殺身亡。"
            "他以繪製政治諷刺漫畫聞名，作品對象涵蓋俄羅斯總統普亭等政治人物，"
            "長期被視為批評克里姆林宮的代表性藝術家。\n\n"
            "—— 本則整理自 Reuters、BBC 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "批普亭俄藝術家波蘭遇刺\n\n"
            "俄羅斯藝術家羅伯特・庫佐夫科夫（筆名謝苗・斯克列佩茨基）在波蘭遭槍殺身亡。"
            "他長期以諷刺漫畫批評俄羅斯政治人物，尤其以描繪普亭的作品最為人所知，"
            "被視為克里姆林宮的批評者。"
            "案件目前正在調查中。\n\n"
            "—— 本則整理自 Reuters、BBC 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "一位俄羅斯藝術家在波蘭被槍殺了。"
            "他叫羅伯特・庫佐夫科夫，用筆名創作諷刺漫畫，"
            "長期批評普亭和克里姆林宮。"
            "他選擇住在波蘭，卻還是遭到了槍擊。"
        ),
        "confidence": "high",
        "opinion_level": "none",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "羅伯特・庫佐夫科夫（筆名謝苗・斯克列佩茨基）在波蘭遭槍殺",
                "source_id": "reuters_world_google_news",
                "source_title": "Russian artist critical of Kremlin shot dead in Poland",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "庫佐夫科夫以繪製包括普亭在內的政治人物諷刺漫畫著稱",
                "source_id": "bbc_world",
                "source_title": "Russian artist known for caricatures of Putin shot dead in Poland",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    # ── ARTS ──────────────────────────────────────────────────────────────

    "daily_20260617_evt_011": {
        "headline": "本週英倫藝評四則",
        "context": (
            "本週《衛報》藝評涵蓋四個文化事件："
            "紀錄片《鸚鵡鸚鵡入侵》探索英國城市中的野生長尾小鸚鵡與階級政治；"
            "《烏托邦的用途》追溯從湯瑪斯・摩爾到娥蘇拉・勒瑰恩的烏托邦思想史；"
            "休・傑克曼主演的《羅賓漢之死》將傳奇英雄刻畫成自私的罪犯；"
            "柯克舞台劇《約瑟夫・葛瑞斯的返鄉》則描繪一名誤打誤撞成為士兵的男人故事。"
        ),
        "thread_text": (
            "本週英倫藝評四則\n\n"
            "《鸚鵡鸚鵡入侵》：Chris Packham 執導的紀錄片，記錄螢光綠長尾小鸚鵡在英國城市擴散，"
            "並以階級戰爭視角切入詮釋。\n\n"
            "《烏托邦的用途》：作者 Joad Raymond Wren 爬梳從湯瑪斯・摩爾到娥蘇拉・勒瑰恩的烏托邦思想脈絡。\n\n"
            "《羅賓漢之死》：休・傑克曼主演，將羅賓漢詮釋為一個自私的罪犯，顛覆英雄形象。\n\n"
            "《約瑟夫・葛瑞斯的返鄉》：柯克 Marina Market 劇院舞台劇，"
            "Deirdre Kinahan 編劇，講述一名誤成士兵的男人故事。\n\n"
            "—— 本則整理自 The Guardian 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "本週英倫藝評四則\n\n"
            "《鸚鵡鸚鵡入侵》：Chris Packham 執導，紀錄螢光綠長尾小鸚鵡如何入侵英國都市，"
            "以階級政治視角切入，讀來令人玩味。\n\n"
            "《烏托邦的用途》：學者 Joad Raymond Wren 帶你從湯瑪斯・摩爾一路走到娥蘇拉・勒瑰恩，"
            "梳理烏托邦思想的演變。\n\n"
            "《羅賓漢之死》：休・傑克曼主演，這版羅賓漢不是英雄，而是個自私的罪犯——"
            "部分觀眾與評論者覺得這個詮釋還不夠到位。\n\n"
            "《約瑟夫・葛瑞斯的返鄉》：柯克 Marina Market 劇院演出，"
            "Deirdre Kinahan 的劇本描繪一個誤入戰場的普通人如何面對命運。\n\n"
            "—— 本則整理自 The Guardian 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "本週英國文化版有四件事值得聊聊。"
            "先說紀錄片——有部影片在拍英國城市裡那些螢光綠小鸚鵡，"
            "導演用階級政治的視角來看這些「外來鳥」，很有趣。"
            "書的部分，有本書從湯瑪斯・摩爾一路追到科幻作家勒瑰恩，"
            "整理烏托邦思想幾百年的脈絡。"
            "電影方面，休・傑克曼演了一個很不一樣的羅賓漢——不是俠盜，而是個自私的罪犯。"
            "最後，愛爾蘭柯克有齣新戲，講一個陰錯陽差成了士兵的男人，聽起來很有張力。"
        ),
        "confidence": "high",
        "opinion_level": "light_context",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "《鸚鵡鸚鵡入侵》紀錄片由 Chris Packham 執導，以階級戰爭框架呈現英國都市鸚鵡問題",
                "source_id": "guardian_culture",
                "source_title": "Invasion of the Parakeets review",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "《烏托邦的用途》追溯從湯瑪斯・摩爾到娥蘇拉・勒瑰恩的烏托邦思想史",
                "source_id": "guardian_books",
                "source_title": "The Uses of Utopia review",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "《羅賓漢之死》由休・傑克曼主演，將主角詮釋為自私的罪犯",
                "source_id": "guardian_film",
                "source_title": "The Death of Robin Hood review",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "《約瑟夫・葛瑞斯的返鄉》由 Deirdre Kinahan 編劇，在柯克 Marina Market 演出",
                "source_id": "guardian_stage",
                "source_title": "The Homecoming of Joseph Grace review",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_003": {
        "headline": "史匹柏新片《揭露日》稱霸票房",
        "context": (
            "史蒂芬・史匹柏執導的外星人驚悚片《揭露日》登上票房冠軍，"
            "由艾蜜莉・布朗特主演。"
            "布朗特坦言從小看史匹柏電影長大，受邀合作時費盡力氣才保持鎮定。"
            "不過部分觀眾與影評認為，這部作品並非他職涯的最佳之作。"
        ),
        "thread_text": (
            "史匹柏新片《揭露日》稱霸票房\n\n"
            "史蒂芬・史匹柏執導的外星人驚悚片《揭露日》拿下票房冠軍，"
            "由艾蜜莉・布朗特擔綱主演。"
            "布朗特透露，她從小看史匹柏電影長大，收到合作邀請時費盡力氣才讓自己冷靜下來。"
            "然而部分觀眾與影評也指出，這部作品稱不上他職涯中最精彩的一頁。\n\n"
            "—— 本則整理自 The New York Times、The Guardian 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "史匹柏新片《揭露日》稱霸票房\n\n"
            "史蒂芬・史匹柏最新執導的外星人驚悚片《揭露日》登上票房冠軍，"
            "由艾蜜莉・布朗特主演。"
            "布朗特在訪問中坦承，她從小看史匹柏電影長大，"
            "真正收到合作邀請的那一刻，她費了很大力氣才讓自己保持鎮定。"
            "不過也有觀眾和影評人認為，"
            "儘管票房亮眼，這部電影未必是史匹柏職涯中最精彩的代表作。\n\n"
            "—— 本則整理自 The New York Times、The Guardian 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "史匹柏的新片《揭露日》拿下票房冠軍了。"
            "艾蜜莉・布朗特主演，是一部外星人驚悚片。"
            "布朗特說，她從小看史匹柏電影長大，"
            "真的拿到邀約的時候，整個人激動到要努力才能讓自己冷靜。"
            "不過批評的聲音也有，有些人覺得這不是他最好的作品。"
        ),
        "confidence": "high",
        "opinion_level": "light_context",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "《揭露日》由史匹柏執導、艾蜜莉・布朗特主演，登上票房冠軍",
                "source_id": "nyt_arts",
                "source_title": "Emily Blunt stars in Disclosure Day, Spielberg alien thriller",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "部分觀眾和影評認為這不是史匹柏職涯最精彩的作品",
                "source_id": "guardian_film",
                "source_title": "Disclosure Day review – Spielberg's alien thriller",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_111": {
        "headline": "Twitch 創作者談成長歲月",
        "context": (
            "TwitchCon 在鹿特丹舉行，許多創作者整個成年生活都在這個平台上度過，"
            "直播給了他們一個得以做自己的空間。"
            "同場，導演班・瑞弗斯獲得唐・德利洛親筆授權，"
            "改編其獨幕劇為電影，故事設定在一個沒有大人、只有九歲女孩背誦神秘台詞的末日世界。"
        ),
        "thread_text": (
            "Twitch 創作者談成長歲月\n\n"
            "TwitchCon 在荷蘭鹿特丹舉行。"
            "許多參與的創作者談及，他們整個成年生活都是在 Twitch 上度過的，"
            "直播給了他們一個空間，得以在觀眾面前做真實的自己。\n\n"
            "另有導演班・瑞弗斯收到唐・德利洛親筆來信，"
            "授權他將一部獨幕劇改編成電影。"
            "故事設定於沒有大人的末日世界，九歲女孩們背誦著德利洛式的神秘台詞。\n\n"
            "—— 本則整理自 The Guardian 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "Twitch 創作者談成長歲月\n\n"
            "TwitchCon 於荷蘭鹿特丹舉行，許多創作者在現場談到，"
            "他們整個成年人生幾乎都在 Twitch 上度過，"
            "這個平台給了他們一個空間——得以在鏡頭前做最真實的自己。\n\n"
            "同一時間，英國導演班・瑞弗斯收到了作家唐・德利洛的親筆信，"
            "授權他將一部獨幕劇改編成電影。"
            "故事世界中沒有任何大人，只有九歲女孩們，"
            "反覆背誦著充滿德利洛風格的神秘對白。\n\n"
            "—— 本則整理自 The Guardian 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "這次 TwitchCon 在鹿特丹舉辦，創作者們聊了很多關於成長的事。"
            "有不少人說，他們整個成年生活都是在這個平台上過的，"
            "直播讓他們有地方可以做自己。"
            "然後還有一件事很有意思——有位導演收到了老作家唐・德利洛的親筆信，"
            "允許他把一部獨幕劇拍成電影。"
            "那個故事的世界裡沒有大人，只有九歲的女孩，"
            "到處背誦著很晦澀的台詞，光聽描述就覺得很詭異。"
        ),
        "confidence": "high",
        "opinion_level": "light_context",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "TwitchCon 在鹿特丹舉行，創作者表示整個成年生活在平台上度過",
                "source_id": "guardian_culture",
                "source_title": "TwitchCon Rotterdam: creators who grew up on the platform",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "導演班・瑞弗斯收到唐・德利洛授權信，改編其獨幕劇為末日電影",
                "source_id": "guardian_film",
                "source_title": "Ben Rivers adapts Don DeLillo play for film",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_020": {
        "headline": "南非爵士傳奇易卜拉欣辭世",
        "context": (
            "南非爵士鋼琴家與樂團指揮阿布杜拉・易卜拉欣以 91 歲高齡辭世。"
            "他的代表作〈曼能堡〉成為反種族隔離運動的非官方音樂象徵，"
            "尼爾森・曼德拉稱他為「我們的莫札特」。"
            "他的音樂以明朗坦率的旋律線條搭配無畏的即興衝動為人稱道。"
        ),
        "thread_text": (
            "南非爵士傳奇易卜拉欣辭世\n\n"
            "南非爵士鋼琴家與樂團指揮阿布杜拉・易卜拉欣以 91 歲辭世。"
            "他的代表作〈曼能堡〉成為反種族隔離鬥爭的非官方音樂主題，"
            "尼爾森・曼德拉曾稱呼他為「我們的莫札特」。"
            "他的音樂以明朗旋律與無畏即興著稱，影響無數後輩音樂人。\n\n"
            "—— 本則整理自 The New York Times、The Guardian 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "南非爵士傳奇易卜拉欣辭世\n\n"
            "南非爵士鋼琴家與樂團指揮阿布杜拉・易卜拉欣以 91 歲高齡辭世。"
            "他的〈曼能堡〉成為反種族隔離運動的非官方音樂象徵，"
            "尼爾森・曼德拉曾以「我們的莫札特」稱呼他，"
            "足見其在南非文化歷史中的地位。"
            "樂評人形容他的演奏風格：明朗毫無遮掩的旋律線條，加上無所畏懼的即興衝動，"
            "是獨樹一格的聲音。\n\n"
            "—— 本則整理自 The New York Times、The Guardian 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "南非爵士樂壇的一位巨人走了。"
            "阿布杜拉・易卜拉欣，91 歲，鋼琴家兼樂團指揮。"
            "他的〈曼能堡〉那首曲子，曾是反種族隔離運動的音樂象徵。"
            "曼德拉叫他「我們的莫札特」。"
            "他的音樂有一種很特別的質地——旋律很明朗、很直接，"
            "但即興的部分又完全無所畏懼。"
        ),
        "confidence": "high",
        "opinion_level": "light_context",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "阿布杜拉・易卜拉欣以 91 歲辭世，〈曼能堡〉為反種族隔離運動的非官方音樂象徵",
                "source_id": "nyt_arts",
                "source_title": "Abdullah Ibrahim, South African Jazz Legend, Dies at 91",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "曼德拉稱其為「我們的莫札特」，以明朗旋律與無畏即興著稱",
                "source_id": "guardian_culture",
                "source_title": "Abdullah Ibrahim obituary",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    # ── AI ────────────────────────────────────────────────────────────────

    "daily_20260617_evt_063": {
        "headline": "美司法部稱 xAI 攸關國安",
        "context": (
            "全美有色人種協進會就 xAI 在設施附近架設未經許可的污染性燃氣渦輪機提起訴訟，"
            "美國司法部介入，要求法院駁回。"
            "司法部主張 xAI 的運作對包括伊朗戰爭在內的軍事任務不可或缺，"
            "並稱其攸關「國家安全、經濟安全與能源安全」。"
        ),
        "thread_text": (
            "美司法部稱 xAI 攸關國安\n\n"
            "全美有色人種協進會（NAACP）因 xAI 架設未經許可的污染性燃氣渦輪機而提起訴訟。"
            "美國司法部出面要求法院駁回，"
            "理由是 xAI 的運作對軍事任務（包括伊朗戰爭相關行動）不可或缺，"
            "並主張這涉及「國家安全、經濟安全與能源安全」。\n\n"
            "—— 本則整理自 Wired、TechCrunch 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "美司法部稱 xAI 攸關國安\n\n"
            "全美有色人種協進會（NAACP）因 xAI 在設施附近架設未取得許可的污染性燃氣渦輪機提起訴訟。"
            "美國司法部隨即出面要求法院駁回這項訴訟，"
            "主張五角大廈需要 xAI 持續運作，"
            "其業務對軍事任務不可或缺，尤其涉及伊朗戰爭。"
            "司法部將 xAI 定性為「對國家安全、經濟安全與能源安全至關重要」的企業。\n\n"
            "—— 本則整理自 Wired、TechCrunch 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "這個消息很耐人尋味。"
            "有民權團體告了 xAI，說他們違法架設污染性渦輪機。"
            "結果美國司法部出來了，要求駁回訴訟。"
            "理由是：xAI 的運作對軍事任務、對伊朗戰爭的行動不可或缺，"
            "攸關國家安全、經濟安全和能源安全。"
            "一家 AI 公司被政府說是「不可或缺的國安資產」，這個定性很值得記住。"
        ),
        "confidence": "high",
        "opinion_level": "light_context",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "NAACP 就 xAI 未取得許可架設污染性燃氣渦輪機提起訴訟",
                "source_id": "wired_ai",
                "source_title": "DOJ intervenes in NAACP lawsuit against xAI",
                "source_url": "",
                "support_type": "direct"
            },
            {
                "claim": "美國司法部要求駁回訴訟，稱 xAI 對軍事任務不可或缺、攸關國家安全",
                "source_id": "techcrunch_ai",
                "source_title": "DOJ claims xAI is vital to national security",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_293": {
        "headline": "ChatGPT 生成不適圖像事件",
        "context": (
            "BBC 科技播客報導，一段特定的提示詞讓 ChatGPT 生成了令人不安的圖像，"
            "引發外界對 AI 系統內在行為的討論。"
            "由於資訊來源單一且細節有限，此事件的完整背景尚待更多報導確認。"
        ),
        "thread_text": (
            "ChatGPT 生成不適圖像事件\n\n"
            "據報導，一段特定提示詞讓 ChatGPT 生成了令人不安的圖像，"
            "此事引發外界對 AI 系統到底「知道什麼」的討論。"
            "目前細節仍有限，相關討論見於 BBC 科技播客節目。\n\n"
            "—— 本則來自 BBC 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "ChatGPT 生成不適圖像事件\n\n"
            "據報導，有人找到了一段特定提示詞，讓 ChatGPT 生成了令人不安的圖像。"
            "此事引發了關於 AI 系統內在機制的提問："
            "這件事告訴我們，這些模型究竟「知道」什麼？"
            "目前詳情有限，出自 BBC 科技播客。目前的消息指出，更多細節仍待確認。\n\n"
            "—— 本則來自 BBC 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "這件事目前的消息指出還很片段，但還是想提一下。"
            "有人找到一個特定的問法，讓 ChatGPT 生成了讓人很不舒服的圖像。"
            "這件事讓人開始想：AI 到底「知道」什麼、又藏著什麼？"
            "細節現在還不多，之後應該會有更多討論。"
        ),
        "confidence": "low",
        "opinion_level": "light_context",
        "single_source_warning": True,
        "claim_trace": [
            {
                "claim": "特定提示詞導致 ChatGPT 生成令人不安的圖像",
                "source_id": "bbc_technology",
                "source_title": "BBC Tech Life: ChatGPT disturbing images prompt",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_046": {
        "headline": "Anthropic 與白宮對峙未解",
        "context": (
            "Anthropic 高層飛赴華盛頓特區，與白宮官員進行高層會談。"
            "然而在會談結束後，雙方對 Claude Fable 5 所帶來的風險仍存有明顯分歧，"
            "尚未達成共識。"
            "由於目前僅有單一消息來源，具體細節有待更多報導確認。"
        ),
        "thread_text": (
            "Anthropic 與白宮對峙未解\n\n"
            "Anthropic 高層親赴華盛頓特區，於本週一與白宮官員舉行高層會談。"
            "然而會談結束後，雙方對 Claude Fable 5 潛在風險的評估仍存在明顯分歧，"
            "未能達成共識。\n\n"
            "—— 本則來自 Wired 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "Anthropic 與白宮對峙未解\n\n"
            "Anthropic 高層親赴華盛頓特區，週一與白宮官員展開高層會談。"
            "這場會談的核心議題是 Claude Fable 5 的風險評估。"
            "然而在高層會談結束之後，雙方對這款模型所帶來風險的判斷依然分歧，"
            "雙方尚未取得共識。此消息目前僅有單一來源報導。\n\n"
            "—— 本則來自 Wired 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "目前的消息指出，Anthropic 和白宮之間的分歧還沒解決。"
            "高層特地飛去華盛頓開會，討論的是 Claude Fable 5 的風險。"
            "但會談開完，雙方的立場還是有落差，沒有談攏。"
            "這個消息目前只有一家媒體報導，細節還不算完整。"
        ),
        "confidence": "medium",
        "opinion_level": "none",
        "single_source_warning": True,
        "claim_trace": [
            {
                "claim": "Anthropic 高層赴華盛頓與白宮會談，雙方對 Claude Fable 5 風險仍有分歧",
                "source_id": "wired_ai",
                "source_title": "Anthropic Is Still at Odds With the White House Over Claude Fable 5",
                "source_url": "https://www.wired.com/story/anthropic-is-still-at-odds-with-the-white-house-over-claude-fable-5/",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_098": {
        "headline": "馬來西亞 AI 新創 Respond.io 融資",
        "context": (
            "馬來西亞新創公司 Respond.io 利用 AI 代理人處理大量客服詢問，"
            "採用「按對話計費」而非傳統「按席次計費」的商業模式。"
            "公司本輪融資 6,250 萬美元（約新台幣 19 億），"
            "並計畫以此推動收購。"
            "目前此消息僅有單一來源報導。"
        ),
        "thread_text": (
            "馬來西亞 AI 新創 Respond.io 融資\n\n"
            "馬來西亞新創 Respond.io 使用 AI 代理人處理大量客服詢問，"
            "以「按對話計費」取代傳統按席次收費的模式。"
            "公司宣布完成 6,250 萬美元（約新台幣 19 億）融資，並計畫用於收購。\n\n"
            "—— 本則來自 TechCrunch 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "馬來西亞 AI 新創 Respond.io 融資\n\n"
            "馬來西亞新創公司 Respond.io 以 AI 代理人處理企業客服詢問，"
            "商業模式的差異在於：他們採「按對話計費」，而非傳統的按席次收費。"
            "公司宣布完成 6,250 萬美元（約新台幣 19 億）的融資，"
            "並表示計畫利用這筆資金進行收購，加速擴張。"
            "此消息目前僅有單一媒體報導。\n\n"
            "—— 本則來自 TechCrunch 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "目前的消息指出，馬來西亞有個 AI 新創公司叫 Respond.io，"
            "專門用 AI 代理人幫企業處理大量客服對話。"
            "他們的計費方式很特別——不是按人頭算，而是按每一次對話收費。"
            "這輪他們融了 6,250 萬美元——約新台幣 19 億，"
            "接下來打算用這筆錢做收購。"
        ),
        "confidence": "medium",
        "opinion_level": "none",
        "single_source_warning": True,
        "claim_trace": [
            {
                "claim": "Respond.io 融資 6,250 萬美元，採按對話計費模式，計畫推動收購",
                "source_id": "techcrunch_ai",
                "source_title": "Malaysia's Respond.io raises $62.5M",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    # ── ECON ──────────────────────────────────────────────────────────────

    "daily_20260617_evt_015": {
        "headline": "日本央行升息至 31 年高點",
        "context": (
            "日本央行將短期政策利率從 0.75% 上調至 1%，創 31 年來新高，並暗示後續仍可能繼續升息。"
            "此舉是在伊朗戰爭通膨壓力、美國施壓與日圓持續走弱的背景下決定的，"
            "且與首相高市早苗的意願相悖。"
            "相比之下，美聯準會與英格蘭銀行預計按兵不動。"
        ),
        "thread_text": (
            "日本央行升息至 31 年高點\n\n"
            "日本央行將短期政策利率由 0.75% 上調至 1%，創下 31 年來新高，"
            "並警告企業正以「相當快的速度」將能源成本轉嫁給彼此。"
            "這項決定是在伊朗戰爭通膨、美國壓力及日圓走弱的背景下做出，"
            "且違背首相高市早苗的意願。"
            "相較之下，美聯準會與英格蘭銀行預計此次均按兵不動。\n\n"
            "—— 本則整理自 Reuters、The Guardian、The New York Times 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "日本央行升息至 31 年高點\n\n"
            "日本央行將短期政策利率從 0.75% 上調至 1%，創下 31 年來最高水準，"
            "同時示警，企業間正以「相當快的速度」相互轉嫁上漲的能源成本。"
            "這項決定是在伊朗戰爭帶來的通膨壓力、美國外部施壓和日圓持續貶值的背景下做出，"
            "且與首相高市早苗的政策立場相悖。"
            "此次會議，美聯準會與英格蘭銀行預計均將維持利率不變。\n\n"
            "—— 本則整理自 Reuters、The Guardian、The New York Times 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "日本央行升息了，利率來到 1%，是 31 年來最高的水準。"
            "背後的壓力很多：伊朗戰爭帶來的通膨、美國的施壓、日圓一直在貶值。"
            "央行還警告，企業正在很快地把成本轉嫁出去。"
            "這個決定跟首相高市早苗的意願不一樣，算是央行獨立性的一次展現。"
            "反觀美國聯準會跟英國央行，這次應該都不會動。"
        ),
        "confidence": "high",
        "opinion_level": "light_context",
        "single_source_warning": False,
        "claim_trace": [
            {
                "claim": "日本央行將短期政策利率上調至 1%，創 31 年高點",
                "source_id": "reuters_world_google_news",
                "source_title": "Bank of Japan raises rates to 31-year high, flags more to come - Reuters",
                "source_url": "https://news.google.com/rss/articles/CBMitwFBVV95cUxPY3g0RV9ZYVZhWG1HQzEyLVU3MU1PQnduNndhaERJN0dTcWVrYUs3YXFEQ1k4NXFsdllBdDJZOHRGSEt4cy1tV3JnZGJfSVVCdFFxNFppZ2YxN3kxZ2VEa2JpU3phbTFDVllJRVEtNnM2VEFHNTZST2dLeTQxY1N1ODJqMlRZZVlfdUcySllSVU5JREJZSWp1RUdiTko3TnYtUktwdzZhMWNrM0ZHbU0tcXByYU1YZVk?oc=5",
                "support_type": "direct"
            },
            {
                "claim": "升息決定在伊朗戰爭通膨壓力下做出，企業快速轉嫁成本",
                "source_id": "guardian_business",
                "source_title": "Bank of Japan raises interest rates to 31-year high … of 1%",
                "source_url": "https://www.theguardian.com/business/2026/jun/16/bank-of-japan-raises-interest-rates-iran-war-inflation-us-fed-bank-of-england",
                "support_type": "direct"
            },
            {
                "claim": "升息違背首相高市早苗意願，同時受美國壓力與日圓走弱影響",
                "source_id": "nyt_business",
                "source_title": "Japan Raises Rates to 31-Year High to Ward Off War Inflation",
                "source_url": "https://www.nytimes.com/2026/06/16/business/japan-interest-rates-war.html",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_036": {
        "headline": "廢鋁出口激增衝擊英國供應鏈",
        "context": (
            "英國業界團體警告，廢鋁出口量大幅攀升，"
            "可能危及英國國防與汽車產業的供應鏈。"
            "目前此消息來源單一，細節有限。"
        ),
        "thread_text": (
            "廢鋁出口激增衝擊英國供應鏈\n\n"
            "英國業界團體提出警告，廢鋁出口急遽增加，"
            "恐對英國國防產業及汽車供應鏈造成威脅。\n\n"
            "—— 本則來自 Reuters 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "廢鋁出口激增衝擊英國供應鏈\n\n"
            "英國業界團體發出警告，廢鋁出口量急遽上升，"
            "可能對英國的國防工業及汽車製造供應鏈構成威脅。"
            "此消息目前僅有單一來源，詳細背景有待更多報導補充。\n\n"
            "—— 本則來自 Reuters 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "目前的消息指出，英國有業界團體在發警報：廢鋁出口量暴增，"
            "可能讓國防和汽車產業的供應鏈出現缺口。"
            "這個消息的細節目前還不多，但供應鏈安全一向是牽一髮動全身的事。"
        ),
        "confidence": "low",
        "opinion_level": "none",
        "single_source_warning": True,
        "claim_trace": [
            {
                "claim": "英國業界團體警告廢鋁出口激增，威脅國防與汽車供應鏈",
                "source_id": "reuters_world_google_news",
                "source_title": "Soaring scrap aluminium exports threaten UK defence and auto supply chains",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_062": {
        "headline": "印度盧比走揚待伊美和談細節",
        "context": (
            "印度盧比持續升值，市場正等待美伊和平協議的具體內容，"
            "以及美聯準會的下一步利率指引。"
            "目前此消息來源單一，細節有限。"
        ),
        "thread_text": (
            "印度盧比走揚待伊美和談細節\n\n"
            "印度盧比持續走強，市場正等待美國與伊朗和平協議的細節，"
            "同時關注美聯準會的最新利率指引。\n\n"
            "—— 本則來自 Reuters 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "印度盧比走揚待伊美和談細節\n\n"
            "印度盧比持續延伸漲勢，市場目前的注意力集中在兩件事上："
            "美國與伊朗之間和平協議的具體條款，以及美聯準會接下來的利率方向。"
            "此消息目前僅有單一來源報導。\n\n"
            "—— 本則來自 Reuters 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "目前的消息指出，印度盧比最近持續在漲。"
            "市場在等兩件事：一是美伊和談的細節確認，"
            "二是美聯準會的利率決定。"
            "這兩個消息都還沒落地，所以市場目前是觀望狀態。"
        ),
        "confidence": "low",
        "opinion_level": "none",
        "single_source_warning": True,
        "claim_trace": [
            {
                "claim": "印度盧比走揚，市場等待美伊和談細節與聯準會利率指引",
                "source_id": "reuters_world_google_news",
                "source_title": "Indian rupee extends gains; awaiting Iran-US deal and Fed guidance",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

    "daily_20260617_evt_064": {
        "headline": "日銀升息觸三十一年新高",
        "context": (
            "日本銀行宣布上調利率，創下 31 年來最高水準，"
            "此舉在市場預期之內。"
            "目前此消息僅有單一來源報導，詳細背景可參閱同日 evt_015 的多來源報導。"
        ),
        "thread_text": (
            "日銀升息觸三十一年新高\n\n"
            "日本銀行宣布升息，將利率調升至 31 年來最高水準。"
            "此次升息幅度與市場預期吻合。\n\n"
            "—— 本則來自 Reuters 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "threads_text": (
            "日銀升息觸三十一年新高\n\n"
            "日本銀行宣布升息，利率來到 31 年來最高水準。"
            "此次升息在市場廣泛預期之內，屬於「如期而至」的決定。\n\n"
            "—— 本則來自 Reuters 於 2026 年 6 月 17 日發佈的報導。"
        ),
        "voice_text": (
            "目前的消息指出，日本央行把利率升到了 31 年來的最高點。"
            "這個動作市場早有預期，不算意外。"
            "如果想了解更完整的背景，可以參考今天日本央行那則更詳細的報導。"
        ),
        "confidence": "medium",
        "opinion_level": "none",
        "single_source_warning": True,
        "claim_trace": [
            {
                "claim": "日本銀行升息至 31 年高點，為市場廣泛預期的舉措",
                "source_id": "reuters_world_google_news",
                "source_title": "BOJ raises interest rates to 31-year high in widely expected move",
                "source_url": "",
                "support_type": "direct"
            }
        ]
    },

}


def update_event_file(event_id: str, updates: dict) -> bool:
    filepath = os.path.join(EVENTS_DIR, f"{event_id}.json")
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Fields to update (only these, never touch the rest)
    allowed_fields = {
        "headline", "context", "thread_text", "threads_text",
        "voice_text", "confidence", "opinion_level", "claim_trace",
        "single_source_warning"
    }

    for key, value in updates.items():
        if key in allowed_fields:
            data[key] = value
        else:
            print(f"[WARN] Skipping disallowed field: {key}")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Updated: {event_id}")
    return True


if __name__ == "__main__":
    success = 0
    fail = 0
    for event_id, updates in REWRITES.items():
        if update_event_file(event_id, updates):
            success += 1
        else:
            fail += 1

    print(f"\nDone. {success} updated, {fail} failed.")
