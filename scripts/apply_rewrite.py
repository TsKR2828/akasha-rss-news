#!/usr/bin/env python3
"""Apply rewritten content to event JSON files."""
import json, pathlib

DATE = "2026-06-19"
EVENTS_DIR = pathlib.Path(f"data/events/{DATE}")

REWRITES = {}

REWRITES["daily_20260619_evt_088"] = {
    "headline": "停火後逾千名巴勒斯坦人遇難",
    "context": "以色列去年十月與哈馬斯達成停火協議後，仍持續在加薩展開軍事行動。加薩衛生部統計，至今已有超過一千名巴勒斯坦人遇難，數字本週突破千人門檻，加薩城週三再遭無人機襲擊。",
    "thread_text": "🧵 1/1\n📌 國際\n\n停火後加薩逾千人遇難\n\n加薩衛生部統計，自以色列與哈馬斯（Hamas）去年十月簽署停火協議以來，至少一千零七名巴勒斯坦人在以色列行動中罹難。這個數字本週突破千人大關。週三，加薩城再遭無人機攻擊，至少三人死亡。\n\n—— 本則整理自 NPR、Al Jazeera 與 Reuters 於 2026 年 6 月 18 至 19 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "加薩衛生部統計，自以色列與哈馬斯（Hamas）去年十月簽署停火協議以來，至少一千零七名巴勒斯坦人在以色列行動中罹難。這個數字本週突破千人大關。週三，加薩城再遭無人機攻擊，至少三人死亡。\n\n本則整理自 NPR、Al Jazeera 與 Reuters 於 2026 年 6 月 18 至 19 日發佈的報導。",
    "voice_text": "停火協議之後，加薩的死亡人數突破了一千人。加薩衛生部的數字顯示，自去年十月以色列與哈馬斯（Hamas）達成停火以來，至少一千零七名巴勒斯坦人在以色列的行動中遇難。這個數字週三又增加了——加薩城發生了無人機攻擊，至少三人罹難。停火之後的傷亡，就是這樣一條一條加進去的。",
    "confidence": "high", "opinion_level": "none",
    "claim_trace": [
        {"claim": "加薩衛生部：停火後至少 1,007 名巴勒斯坦人遇難", "source_id": "aljazeera_all", "source_title": "Israel kills at least three Palestinians in Gaza City drone strike", "source_url": "https://www.aljazeera.com/news/2026/6/18/israel-kills-at-least-three-palestinians-in-gaza-city-drone-strike?traffic_source=rss", "support_type": "direct"},
        {"claim": "加薩停火後死亡人數突破千人", "source_id": "npr_world", "source_title": "Over 1,000 people killed during Gaza ceasefire, Palestinian authorities say", "source_url": "https://www.npr.org/2026/06/18/g-s1-128734/over-1-000-people-killed-during-gaza-ceasefire-palestinian-authorities-say", "support_type": "direct"},
        {"claim": "以色列加薩停火後死亡人數超千", "source_id": "reuters_world_google_news", "source_title": "Death toll from Israeli fire in Gaza since ceasefire passes 1,000, says health ministry - Reuters", "source_url": "https://news.google.com/rss/articles/CBMiywFBVV95cUxPSFYySXA3T3Y0ZEN5Y2dBelZRLUp5UmtNWW9jVUJ3eUM1d1JRbzBJcl8weUpZWDF3Z1BublZzRGt6VlJTU3djWmFYOE9mQlJNaVBiQzd1eTR6QXJtTFJnekp6X3VtZWFqczNrMXE1OWxOOE5NTHFMMTBhcnZ1S050WHFCbzk4NUJJVzV4c3VJX2FxdE5sNHZGTF9jU1JBaDl0QXVlSGwtM0QwYnd5bC1UQ0J4WkJhSHdiWnk3NTM4cTBxTFBTUUhmUkl2SQ?oc=5", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_119"] = {
    "headline": "美宣布審查駐歐兵力",
    "context": "美國國防部長 Pete Hegseth 在布魯塞爾（Brussels）北約（NATO）會議上砲轟盟友，宣布將審查美軍駐歐規模，並提出「NATO 3.0」改革方向。",
    "thread_text": "🧵 1/1\n📌 國際\n\nHegseth 砲轟盟國，喊出 NATO 3.0\n\n美國國防部長 Pete Hegseth 在布魯塞爾（Brussels）宣布要審查美軍駐歐兵力，並要求北約（NATO）進行重大改革，將組織「重開機」成 NATO 3.0。他直接批評現有盟友，語氣強硬。\n\n—— 本則整理自 NPR 與 Reuters 於 2026 年 6 月 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "美國國防部長 Pete Hegseth 在布魯塞爾（Brussels）宣布要審查美軍駐歐兵力，並要求北約（NATO）進行重大改革，將組織「重開機」成 NATO 3.0。他直接砲轟現有盟國，語氣強硬。歐洲對美國安全承諾原本就有疑慮，Hegseth 這番話讓局勢更加複雜。\n\n本則整理自 NPR 與 Reuters 於 2026 年 6 月 18 日發佈的報導。",
    "voice_text": "Hegseth 在布魯塞爾砲轟北約（NATO）盟友，宣布要全面審查美軍在歐洲的駐軍規模。美國國防部長 Pete Hegseth 把這套改革方向稱為「NATO 3.0」，意思是北約必須從頭建立一個新框架。這個時間點很微妙——歐洲各國對美國安全承諾本就有疑慮，這番話讓局勢更不穩定。",
    "confidence": "high", "opinion_level": "light_context",
    "claim_trace": [
        {"claim": "Hegseth 在布魯塞爾宣布審查美軍駐歐兵力並提出 NATO 3.0", "source_id": "npr_world", "source_title": "Hegseth announces in Brussels a review of U.S. forces in Europe, and a 'NATO 3.0'", "source_url": "https://www.npr.org/2026/06/18/nx-s1-5862604/hegseth-nato-3-0", "support_type": "direct"},
        {"claim": "Hegseth 猛烈批評北約成員並宣布審查駐歐美軍", "source_id": "reuters_world_google_news", "source_title": "Hegseth blasts NATO members, announces review of US forces in Europe - Reuters", "source_url": "https://news.google.com/rss/articles/CBMipgFBVV95cUxNLTVjVHJMMDNtX0hTZEtYZG1URk9uZkxyaWlDWmJMSFJuNmpkZTFGT0FTOG92Z3U3QWtLaDVTbnhDcGVOYzVsMWd4QmhOdkhoQlFSaWdoMkE4Z3l5eXRKNjlLOUs4dUNsZmtkNjJMTFBweVI5SmJLaEJ6blg0UnFyUXFzWERRd3Q0U2U0RVJVeXEtVmVQaEhyRVdkWTVpeXo0WU5hVGZn?oc=5", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_033"] = {
    "headline": "烏無人機大規模打擊莫斯科",
    "context": "烏克蘭對俄羅斯首都發動大規模無人機攻勢，近兩百架無人機擊中莫斯科東南方，煉油廠和購物中心起火，莫斯科居民報告出現「黑雨」，這是俄烏戰爭以來對俄首都最大規模的打擊之一。",
    "thread_text": "🧵 1/1\n📌 國際\n\n烏無人機大規模打擊莫斯科煉油廠\n\n烏克蘭對俄羅斯首都發動大規模無人機攻勢，近兩百架無人機擊中莫斯科（Moscow）東南方地區，煉油廠與購物中心中彈起火。莫斯科居民記錄到「黑雨」落下——那是煉油廠燃燒後的落塵。這是俄烏戰爭開打四年多以來，烏克蘭對俄首都最大規模的攻擊之一。\n\n—— 本則整理自 Reuters、BBC 與 NPR 於 2026 年 6 月 18 至 19 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "烏克蘭對俄羅斯首都莫斯科（Moscow）發動大規模無人機攻勢，近兩百架無人機擊中莫斯科東南方，煉油廠與購物中心中彈起火。莫斯科居民抱怨「黑雨」從天落下——那是煉油廠燃燒產生的落塵。這是俄烏戰爭開打超過四年以來，對俄羅斯首都規模最大的一次打擊之一。\n\n本則整理自 Reuters、BBC 與 NPR 於 2026 年 6 月 18 至 19 日發佈的報導。",
    "voice_text": "烏克蘭對莫斯科發動了開戰四年多以來規模最大的無人機攻勢之一。近兩百架無人機擊中莫斯科（Moscow）東南方，一座煉油廠和一座購物中心起火燃燒。那天莫斯科居民記錄到「黑雨」從天降落——那是煉油廠大火飄散的落塵。",
    "confidence": "high", "opinion_level": "none",
    "claim_trace": [
        {"claim": "烏克蘭無人機大規模攻擊莫斯科煉油廠", "source_id": "reuters_world_google_news", "source_title": "Ukraine hits Moscow refinery in major drone attack on Russian capital - Reuters", "source_url": "https://news.google.com/rss/articles/CBMipwFBVV95cUxONjIyM051UnloU3UzZVY0RzFIX1JKUzBycnV2OTJkZExlMkc0SE9USXEwcXFjS2J2YXQtU1o4RXFtamJzbjE5RlBySG9mejYyN25oeTdsVkdETkhMaW01Y01Sa1JOR0dwdTUxTUk3bnpSUjZrTVp6ZnhVMjRYOThxNUptdkJuZTJmd3BYMlNYdGlxanRTMDdHT1FMaFdaeTB3NnplNmxjaw?oc=5", "support_type": "direct"},
        {"claim": "煉油廠和購物中心中彈，莫斯科居民抱怨黑雨", "source_id": "bbc_world", "source_title": "Moscow residents complain of black rain after largest Ukrainian attack hits oil refinery", "source_url": "https://www.bbc.com/news/articles/c98291g5rr1o?at_medium=RSS&at_campaign=rss", "support_type": "direct"},
        {"claim": "烏克蘭對俄羅斯首都發動規模最大無人機攻勢之一", "source_id": "npr_world", "source_title": "Ukraine hits a Moscow oil refinery and other sites in a large-scale drone attack", "source_url": "https://www.npr.org/2026/06/18/g-s1-128782/moscow-ukraine-drone-attack-russia-oil-refinery", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_061"] = {
    "headline": "美伊凡爾賽宮簽停火備忘錄",
    "context": "美國總統川普（Trump）與伊朗總統 Masoud Pezeshkian 在法國凡爾賽宮（Palace of Versailles）G7 晚宴後，聯署了一份十四點停火備忘錄，巴基斯坦總理謝赫巴茲·謝里夫（Shehbaz Sharif）也共同署名。",
    "thread_text": "🧵 1/1\n📌 國際\n\n川普與伊朗在凡爾賽宮簽停火備忘錄\n\n美國總統川普（Trump）與伊朗總統 Masoud Pezeshkian 在法國凡爾賽宮（Palace of Versailles），於七大工業國組織（G7）晚宴後聯署了一份十四點停火備忘錄（Memorandum of Understanding）。巴基斯坦總理謝赫巴茲·謝里夫（Shehbaz Sharif）也以見證方身分共同署名。\n\n—— 本則整理自 BBC、NPR 與 Al Jazeera 於 2026 年 6 月 18 至 19 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "美國總統川普（Trump）與伊朗總統 Masoud Pezeshkian 在法國凡爾賽宮（Palace of Versailles）聯署了一份十四點停火備忘錄（MoU）。時間點在 G7 晚宴之後。巴基斯坦總理謝赫巴茲·謝里夫（Shehbaz Sharif）也以見證方身分共同署名。這是美伊之間的初步停火文件，正式落實情況有待後續確認。\n\n本則整理自 BBC、NPR 與 Al Jazeera 於 2026 年 6 月 18 至 19 日發佈的報導。",
    "voice_text": "美國和伊朗在凡爾賽宮簽了停火文件。美國總統川普（Trump）與伊朗總統 Masoud Pezeshkian，在七大工業國組織（G7）晚宴後，於法國凡爾賽宮聯署了一份十四點備忘錄。巴基斯坦總理謝赫巴茲·謝里夫（Shehbaz Sharif）也跟著簽了名。這份協議目前是初步性質，後續落實仍有待觀察。",
    "confidence": "high", "opinion_level": "none",
    "claim_trace": [
        {"claim": "川普與伊朗在凡爾賽宮簽署停火備忘錄", "source_id": "bbc_world", "source_title": "Moment Trump signs US-Iran agreement at Palace of Versailles", "source_url": "https://www.bbc.com/news/videos/crm03y1xx2no?at_medium=RSS&at_campaign=rss", "support_type": "direct"},
        {"claim": "備忘錄共十四點，由川普與伊朗總統聯署", "source_id": "npr_world", "source_title": "Read the full text of Trump's preliminary U.S.-Iran agreement to end the war", "source_url": "https://www.npr.org/2026/06/18/nx-s1-5863027/us-iran-trump-memorandum-of-understanding-full-text", "support_type": "direct"},
        {"claim": "巴基斯坦簽署美伊停火備忘錄", "source_id": "aljazeera_all", "source_title": "Pakistan signs US-Iran MoU", "source_url": "https://www.aljazeera.com/video/newsfeed/2026/6/18/pakistan-signs-us-iran-mou?traffic_source=rss", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_080"] = {
    "headline": "台灣：未挑釁中國盼軍售過關",
    "context": "台灣總統公開表示台灣並非在「挑釁」中國，並期望美國的對台軍售套案能盡早獲得批准。",
    "thread_text": "🇹🇼 台灣相關 ——\n\n🧵 1/1\n📌 國際\n\n台灣：未挑釁中國，盼美軍售案過關\n\n台灣總統表示，台灣並非在「挑釁」中國，同時希望美方的對台軍售套案能盡早獲得批准。\n\n—— 本則來自 Reuters 於 2026 年 6 月 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "🇹🇼 台灣相關 ——\n\n台灣總統公開表示，台灣並非在「挑釁」中國，並希望美方的對台軍售套案能盡早獲得批准。軍售案的審批程序目前仍在進行中。\n\n本則來自 Reuters 於 2026 年 6 月 18 日發佈的報導。",
    "voice_text": "這則跟台灣有關。台灣總統公開表示，台灣沒有在「挑釁」中國，並期望美方能盡快批准對台軍售套案。目前的消息指出，軍售審批程序正在推進中。",
    "confidence": "medium", "opinion_level": "none",
    "claim_trace": [{"claim": "台灣總統稱台灣未挑釁中國，盼美軍售案獲批", "source_id": "reuters_world_google_news", "source_title": "Taiwan not 'provoking' China, hopes US arms sale package can be approved soon, president says - Reuters", "source_url": "https://news.google.com/rss/articles/CBMixAFBVV95cUxPTkF5c2hhQzRGaVpBRG5MeUlfZEFRY2g5Rk5ibU9mQnB2RXRzQ1J2MlIyNXNHUF9JTndCa0xxLTAxVWo0OWdZOU5ibm9iYWFIRndYRzBmRTNCUHpSMlBPanBjbGx1d3J3alNFcDAycWdrR3kxa2p2bC1RTWpVTXdNeXVGdkdFMFdwWFd3RGlMeGFtb1g4N29SdzFUdVlqdGw2RFltUDlJRjFXMEVZb2puUlU3UnV6c1FENlpfZm5HeVBXTDIw?oc=5", "support_type": "direct"}]
}
REWRITES["daily_20260619_evt_022"] = {
    "headline": "童星 Daveigh Chase 35 歲病逝",
    "context": "曾為迪士尼動畫《星際寶貝》（Lilo & Stitch）中麗蘿（Lilo）配音，並在恐怖電影《七夜怪談》（The Ring）飾演鬼女孩薩瑪拉（Samara Morgan）的美國演員 Daveigh Chase，因腦膜炎引發敗血症，在洛杉磯醫院逝世，享年三十五歲。",
    "thread_text": "🧵 1/1\n📌 藝文\n\n《星際寶貝》聲優 Daveigh Chase 病逝，享年三十五\n\n美國演員 Daveigh Chase 在本週病逝，享年三十五歲。她曾為迪士尼動畫《星際寶貝》（Lilo & Stitch）中的麗蘿（Lilo）配音，也在二○○二年恐怖片《七夜怪談》（The Ring）中飾演鬼女孩薩瑪拉（Samara Morgan）。她的男友表示，死因是腦膜炎引發血液感染，最終導致敗血症，在洛杉磯一家醫院辭世。\n\n—— 本則整理自 The Guardian、BBC 與 The New York Times 於 2026 年 6 月 17 至 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "《星際寶貝》（Lilo & Stitch）中麗蘿（Lilo）的配音員、《七夜怪談》（The Ring）中鬼女孩薩瑪拉（Samara Morgan）的飾演者，美國演員 Daveigh Chase 在本週病逝，享年三十五歲。她的男友表示，死因是腦膜炎引發血液感染，最終導致敗血症，在洛杉磯一家醫院辭世。\n\n本則整理自 The Guardian、BBC 與 The New York Times 於 2026 年 6 月 17 至 18 日發佈的報導。",
    "voice_text": "美國演員 Daveigh Chase 在本週病逝，享年三十五歲。她是《星際寶貝》（Lilo & Stitch）中麗蘿（Lilo）的聲音，也是《七夜怪談》（The Ring）裡那個鬼女孩薩瑪拉（Samara Morgan）。她的男友表示，死因是腦膜炎引發血液感染，最終釀成敗血症，在洛杉磯醫院辭世。",
    "confidence": "high", "opinion_level": "none",
    "claim_trace": [
        {"claim": "Daveigh Chase 因敗血症在洛杉磯逝世，享年三十五", "source_id": "guardian_film", "source_title": "Daveigh Chase, child star known for Lilo & Stitch and The Ring, dies aged 35", "source_url": "https://www.theguardian.com/film/2026/jun/17/daveigh-chase-dies-aged-35", "support_type": "direct"},
        {"claim": "Chase 死於腦膜炎引發的敗血症", "source_id": "bbc_world", "source_title": "The Ring and Lilo & Stitch actress Daveigh Chase dies aged 35", "source_url": "https://www.bbc.com/news/articles/cd0m2mg949yo?at_medium=RSS&at_campaign=rss", "support_type": "direct"},
        {"claim": "她為 Lilo & Stitch 配音並在 The Ring 飾演反派", "source_id": "nyt_arts", "source_title": "Daveigh Chase, 'Lilo & Stitch' Voice Actor and 'The Ring' Villain, Dies at 35", "source_url": "https://www.nytimes.com/2026/06/17/arts/daveigh-chase-dead.html", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_179"] = {
    "headline": "《小小兵》新作即將上映",
    "context": "《小小兵》（Minions）系列導演 Pierre Coffin 開放讀者提問，即將推出系列第七部《小小兵與怪物》（Minions & Monsters），預計在美國國慶日前後上映；靈魂樂傳奇 Martha Reeves 睽違二十二年將發行新專輯，也開放讀者互動。",
    "thread_text": "🧵 1/1\n📌 藝文\n\n《小小兵》第七部將至，導演 Pierre Coffin 征集提問\n\n《小小兵》（Minions）系列第七部《小小兵與怪物》（Minions & Monsters）即將在美國國慶日前後上映。系列至今全球總收入達 123 億英鎊。導演 Pierre Coffin 一手包辦全部小小兵的配音，現開放讀者提問。另外，靈魂樂傳奇 Martha Reeves（Martha and the Vandellas 主唱）年屆八十四，睽違二十二年將發行新專輯，同樣開放讀者互動。\n\n—— 本則整理自 The Guardian 於 2026 年 6 月 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "《小小兵》（Minions）系列導演 Pierre Coffin 即將接受讀者提問。新作《小小兵與怪物》（Minions & Monsters）是該系列第七部，預計在美國國慶日前後上映。Coffin 除執導外也一手包辦所有小小兵配音。整個系列至今全球累積收入達 123 億英鎊。\n\n靈魂樂傳奇 Martha Reeves，她是 Martha and the Vandellas 的主唱，曾以〈Dancing in the Street〉成為美國民權運動的象徵——如今年屆八十四，睽違二十二年將發行新專輯，同樣開放讀者提問。\n\n本則整理自 The Guardian 於 2026 年 6 月 18 日發佈的報導。",
    "voice_text": "《小小兵》系列第七部即將上映。《小小兵與怪物》（Minions & Monsters）預計在美國國慶假期前後亮相。系列導演 Pierre Coffin 不只執導，也是全部小小兵那些嘰哩咕嚕聲音的來源——一個人配了所有角色。這個系列到目前為止全球累積收入達 123 億英鎊。另外，靈魂樂傳奇 Martha Reeves——Martha and the Vandellas 的主唱，八十四歲高齡，將發行睽違二十二年的新專輯。",
    "confidence": "high", "opinion_level": "none",
    "claim_trace": [
        {"claim": "《小小兵與怪物》是系列第七部，系列全球收入達 £12.3bn", "source_id": "guardian_film", "source_title": "Post your questions for Minions supremo Pierre Coffin", "source_url": "https://www.theguardian.com/film/2026/jun/18/post-your-questions-for-minions-supremo-pierre-coffin", "support_type": "direct"},
        {"claim": "Martha Reeves 八十四歲，睽違二十二年將發行新專輯", "source_id": "guardian_culture", "source_title": "Post your questions for Martha Reeves of Martha and the Vandellas", "source_url": "https://www.theguardian.com/music/2026/jun/18/post-your-questions-for-martha-reeves-of-martha-and-the-vandellas", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_038"] = {
    "headline": "老維克全女班版話劇開演",
    "context": "大衛·馬密特（David Mamet）的經典話劇《格倫蓋里·格倫羅斯》（Glengarry Glen Ross）以全女演員陣容在倫敦老維克（Old Vic）劇院搬演，導演 Patrick Marber 表示這個構想來自馬密特本人；另外，英國創作歌手 Myles Smith 發行了新專輯《My Mess, My Heart, My Life》。",
    "thread_text": "🧵 1/1\n📌 藝文\n\n馬密特名劇全女班版在老維克登台\n\n大衛·馬密特（David Mamet）的經典話劇《格倫蓋里·格倫羅斯》（Glengarry Glen Ross），以全女演員陣容在倫敦老維克（Old Vic）劇院搬演，性別對調的構想出自馬密特本人，由 Patrick Marber 執導。評論認為喜劇感提升，但風格有點過頭。另外，英國歌手 Myles Smith 發行新專輯，評論定位他為受 Ed Sheeran 影響的流行民謠路線。\n\n—— 本則整理自 The Guardian 於 2026 年 6 月 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "大衛·馬密特（David Mamet）的名劇《格倫蓋里·格倫羅斯》（Glengarry Glen Ross）在倫敦老維克劇院（Old Vic）以全女演員版本呈現。性別對調的點子本來就來自劇作家本人。導演 Patrick Marber 去年也做過百老匯的全男版，這次轉換陣容重演。評論認為喜劇感強了，但略有過頭之嫌。\n\n另外，英國創作歌手 Myles Smith 發行了新專輯《My Mess, My Heart, My Life》，受 Ed Sheeran 影響明顯，Stargazing 至今仍在英國排行榜前一百名內。\n\n本則整理自 The Guardian 於 2026 年 6 月 18 日發佈的報導。",
    "voice_text": "馬密特（Mamet）的名劇，這次換了全女班重演。大衛·馬密特的《格倫蓋里·格倫羅斯》（Glengarry Glen Ross）是一齣關於一九八〇年代芝加哥男性業務文化的經典，如今在倫敦老維克（Old Vic）劇院由全女演員出演，而且這個性別對調的構想本來就是馬密特自己提的。評論說喜劇感更重，不過有點走向《暴徒們》（Bugsy Malone）的輕巧路線。另一邊，英國創作歌手 Myles Smith 發行了新專輯，受 Ed Sheeran 影響明顯，大眾接受度高。",
    "confidence": "high", "opinion_level": "light_context",
    "claim_trace": [
        {"claim": "《格倫蓋里·格倫羅斯》全女班版在老維克演出，構想來自馬密特本人", "source_id": "guardian_stage", "source_title": "Glengarry Glen Ross review – Mamet's gender-swapped motormouths fail to close the deal", "source_url": "https://www.theguardian.com/stage/2026/jun/18/glengarry-glen-ross-review-old-vic-theatre-david-mamet-patrick-marber", "support_type": "direct"},
        {"claim": "Myles Smith 新專輯 Stargazing 至今仍在英國榜前一百", "source_id": "guardian_music", "source_title": "Myles Smith: My Mess, My Heart, My Life review | Alexis Petridis's album of the week", "source_url": "https://www.theguardian.com/music/2026/jun/18/myles-smith-my-mess-my-heart-my-life-review", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_077"] = {
    "headline": "西班牙薄餐巾成攝影書主角",
    "context": "西班牙餐廳裡那薄到幾乎無用的小餐巾（servilletas），被一本新攝影書視為伊比利半島的文化珍寶；另外，兩部一九七〇年代西班牙電視驚悚短片《電話亭》（La Cabina）與《電視機》（El Televisor）近期以雙片裝形式重映。",
    "thread_text": "🧵 1/1\n📌 藝文\n\n薄到無用的西班牙小餐巾，成了攝影書主角\n\n西班牙餐廳那薄得幾乎什麼都擦不掉的小餐巾（servilletas），被一本新攝影書定義為伊比利半島（Iberian Peninsula）的「文化珍寶」。作者認為它的脆弱和無用是抵抗「效率優化」的奇特符號。另外，西班牙一九七〇年代兩部電視驚悚短片《電話亭》（La Cabina）與《電視機》（El Televisor）以雙片裝形式重映，《電話亭》廣受好評。\n\n—— 本則整理自 The Guardian 於 2026 年 6 月 18 至 19 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "西班牙餐廳那薄到幾乎沒有用的小餐巾（servilletas），正式成了一本新攝影書的主角。作者認為這種紙巾雖在功能上一無是處，卻意外代表了一種對「效率優化」時代的奇妙抵抗，是伊比利半島（Iberian Peninsula）的微型文化符號。\n\n另外，兩部西班牙一九七〇年代電視驚悚短片《電話亭》（La Cabina）與《電視機》（El Televisor）以雙片裝重映。《電話亭》僅三十五分鐘，評論給出極高評價，形容它是一個涵蓋整個焦慮世界的夢魘小品。\n\n本則整理自 The Guardian 於 2026 年 6 月 18 至 19 日發佈的報導。",
    "voice_text": "西班牙那薄到無用的小餐巾，最近成了攝影書的主角。一本新書把伊比利半島（Iberian Peninsula）餐廳裡那些薄得什麼也擦不掉的 servilletas，記錄為一種文化珍寶。作者說，它的無用本身就是一種抵抗——在一個講究效率的年代，這張紙巾固執地什麼都不做。另外，西班牙一九七〇年代的兩部電視驚悚短片《電話亭》（La Cabina）與《電視機》（El Televisor）重映，《電話亭》三十五分鐘，評論評價極高。",
    "confidence": "high", "opinion_level": "light_context",
    "claim_trace": [
        {"claim": "新攝影書將西班牙超薄餐巾記錄為文化珍寶", "source_id": "guardian_art_design", "source_title": "'The beauty of the useless': Spain's super-thin restaurant napkins are throwaway art treasures", "source_url": "https://www.theguardian.com/artanddesign/2026/jun/18/the-beauty-of-the-useless-spains-super-thin-restaurant-napkins-are-throwaway-art-treasures", "support_type": "direct"},
        {"claim": "西班牙電視驚悚短片 La Cabina 重映，評論高度好評", "source_id": "guardian_film", "source_title": "La Cabina/El Televisor review – horror and anxiety on the air and down the line in Franco's Spain", "source_url": "https://www.theguardian.com/film/2026/jun/18/la-cabina-el-televisor-review-horror-on-the-air-and-down-the-line-in-francos-spain", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_001"] = {
    "headline": "AI 帳單來了，企業算 ROI",
    "context": "矽谷「Tokenmaxxing」風潮退燒，Uber 據報幾個月燒光全年 AI 預算，Meta 關掉內部排行榜，部分公司縮減 Claude 授權；創投公司 NEA 合夥人 Tiffany Luck 近期討論 AI 新創 IPO、個人 agent 前景與企業 ROI 重新盤算。",
    "thread_text": "🧵 1/1\n📌 AI\n\nAI 帳單來了，企業開始算 ROI\n\n矽谷（Silicon Valley）今年初流行「Tokenmaxxing」——CEO 催員工把 AI 用到極限。結果帳單來了：Uber 據報幾個月燒光全年 AI 預算，有公司縮了 Claude 授權，Meta 關掉內部 AI 排行榜。創投公司 NEA 的合夥人 Tiffany Luck 近期接受訪談，談到企業正在重新盤算 AI 投資回報（ROI）。\n\n—— 本則來自 TechCrunch 於 2026 年 6 月 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "矽谷今年初流行「Tokenmaxxing」——CEO 鼓勵員工把 AI 用到極限。但帳單到了。據報導，Uber 幾個月內就燒光了整年的 AI 預算；部分公司縮減了 Claude 授權範圍；Meta 則關掉了內部的 AI 使用排行榜。創投公司 NEA 的合夥人 Tiffany Luck 接受訪談，討論 AI 新創 IPO 前景、個人 agent 的機會，以及企業如何面對「AI 到底有沒有回本」這個正在被逼答的問題。\n\n本則來自 TechCrunch 於 2026 年 6 月 18 日發佈的報導。",
    "voice_text": "矽谷的 AI 帳單到了。今年初，「Tokenmaxxing」是矽谷最熱的詞——CEO 催員工把 AI 盡量用。結果幾個月後，Uber 據報燒光了整年的 AI 預算，有公司縮了員工的 Claude 授權，Meta 也關掉了內部的 AI 使用排行榜。創投公司 NEA 的合夥人 Tiffany Luck 最近聊到這個趨勢——企業正在重新盤算 AI 的投資回報，個人 agent 和 AI 新創上市，都是接下來的觀察重點。",
    "confidence": "medium", "opinion_level": "none",
    "claim_trace": [{"claim": "Tokenmaxxing 熱潮後 Uber 燒光全年 AI 預算，Meta 關掉排行榜", "source_id": "techcrunch_ai", "source_title": "NEA's Tiffany Luck on AI IPOs, personal agents, and the ROI reckoning", "source_url": "https://techcrunch.com/podcast/neas-tiffany-luck-on-ai-ipos-personal-agents-and-the-roi-reckoning/", "support_type": "direct"}]
}
REWRITES["daily_20260619_evt_036"] = {
    "headline": "白宮命撤 SK 電信 AI 存取權",
    "context": "白宮聲稱韓國電信業者 SK 電信（SK Telecom）與中國存在關聯，下令 Anthropic（安索比克）撤銷 SK 電信對旗下頂尖 AI 模型 Claude Mythos 的存取授權，事件發生在 Anthropic 將數款進階模型下線前幾天。",
    "thread_text": "🧵 1/1\n📌 AI\n\n白宮命令 Anthropic 切斷 SK 電信的 AI 存取\n\n白宮向 AI 公司 Anthropic（安索比克）下令，要求撤銷韓國電信業者 SK 電信（SK Telecom）對旗下頂端模型 Claude Mythos 的存取授權。理由是白宮聲稱 SK 電信與中國存在關聯。這件事發生在 Anthropic 將數款進階 AI 模型暫時下線的幾天前。\n\n—— 本則來自 Wired 於 2026 年 6 月 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "白宮向 AI 公司 Anthropic（安索比克）下令，要求撤銷韓國電信業者 SK 電信（SK Telecom）對旗下最高端模型 Claude Mythos 的存取授權，理由是聲稱 SK 電信與中國有所關聯。這件事發生在 Anthropic 將幾款頂尖 AI 模型暫時下線的前幾天，涉及美國 AI 出口管制的敏感考量。\n\n本則來自 Wired 於 2026 年 6 月 18 日發佈的報導。",
    "voice_text": "美國白宮下令撤銷 SK 電信（SK Telecom）對 Anthropic（安索比克）頂尖 AI 模型的存取。白宮聲稱韓國電信業者 SK 電信與中國存在關聯，要求 Anthropic 終止該公司對 Claude Mythos 的使用授權。目前的消息指出，這件事發生在 Anthropic 將幾款進階模型下線前幾天，背後涉及美國對 AI 出口管制的敏感地帶。",
    "confidence": "medium", "opinion_level": "none",
    "claim_trace": [{"claim": "白宮命令 Anthropic 撤銷 SK 電信 Claude Mythos 存取，理由是涉嫌中國關聯", "source_id": "wired_ai", "source_title": "The Korean Telecom Giant at the Center of Anthropic's Mythos Controversy", "source_url": "https://www.wired.com/story/sk-telecom-anthropic-mythos-export-controls/", "support_type": "direct"}]
}
REWRITES["daily_20260619_evt_053"] = {
    "headline": "教你關掉 Gemini AI 彈出提示",
    "context": "Google 文件（Google Docs）的 Gemini AI 寫作彈窗讓不少用戶感到困擾，目前有方法可以在設定中將它關閉。",
    "thread_text": "🧵 1/1\n📌 AI\n\n教你關掉 Google Docs 的 Gemini 提示\n\nGoogle 文件（Google Docs）裡的 AI 寫作功能 Gemini 老是跳出「用 Gemini 寫作」的視窗讓人煩惱。目前有方法可以在設定中把它關掉，操作步驟不複雜。\n\n—— 本則來自 TechCrunch 於 2026 年 6 月 17 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "Google 文件（Google Docs）內建的 Gemini AI 寫作提示，常讓不少用戶覺得礙眼。如果你不想再看到「用 Gemini 寫作」的彈出視窗，目前已有方法在設定中將它關閉，操作流程不複雜。\n\n本則來自 TechCrunch 於 2026 年 6 月 17 日發佈的報導。",
    "voice_text": "Google 文件的 Gemini 提示可以關掉。Google 文件（Google Docs）裡一直跳出「用 Gemini 寫作」視窗的問題，現在有方法在設定中解決，幾個步驟就能把它關閉。",
    "confidence": "medium", "opinion_level": "none",
    "claim_trace": [{"claim": "可在設定中關閉 Google Docs 的 Gemini AI 提示", "source_id": "techcrunch_ai", "source_title": "How to turn off AI in your Google Docs", "source_url": "https://techcrunch.com/2026/06/17/how-to-turn-off-ai-in-your-google-docs/", "support_type": "direct"}]
}
REWRITES["daily_20260619_evt_174"] = {
    "headline": "Pixi 推 AR 訊息新體驗",
    "context": "新創公司 Pixi 推出 iOS 應用程式，將文字訊息轉換成可互動的擴增實境（AR）體驗，定位為貼圖和 GIF 之後的下一代訊息形式。",
    "thread_text": "🧵 1/1\n📌 AI\n\nPixi 新 App：把文字訊息變成 AR 體驗\n\n新創公司 Pixi 推出 iOS 應用程式，讓文字訊息以擴增實境（AR）形式呈現，定位為貼圖、GIF 和表情符號之後的下一代訊息互動介面。\n\n—— 本則來自 TechCrunch 於 2026 年 6 月 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "新創公司 Pixi 推出了一款 iOS 應用程式，把文字訊息轉換成可互動的擴增實境（AR）體驗。Pixi 的構想是：繼貼圖、GIF 和表情符號之後，下一個訊息形式的演化就是 AR。\n\n本則來自 TechCrunch 於 2026 年 6 月 18 日發佈的報導。",
    "voice_text": "Pixi 是一款讓文字訊息變成擴增實境（AR）體驗的新 iOS 應用程式。這家新創公司的構想是：貼圖、GIF 和表情符號之後，訊息的下一步演化是互動式 AR。目前的消息指出這款 app 已在 iOS 上推出。",
    "confidence": "medium", "opinion_level": "none",
    "claim_trace": [{"claim": "Pixi 推出 iOS app，將文字訊息轉為互動 AR 體驗", "source_id": "techcrunch_ai", "source_title": "Pixi's new iOS app turns text messages into interactive AR experiences", "source_url": "https://techcrunch.com/2026/06/18/pixis-new-ios-app-turns-text-messages-into-interactive-ar-experiences/", "support_type": "direct"}]
}
REWRITES["daily_20260619_evt_184"] = {
    "headline": "英央行利率凍結通膨警示",
    "context": "英國央行（Bank of England）宣布維持利率在 3.75%，上次降息為去年十二月。行長 Andrew Bailey 表示，中東衝突推高了能源成本，儘管美伊剛簽停火協議、油價有所回落，通膨壓力仍未消散，今年英國民眾預期面對更高生活成本。",
    "thread_text": "🧵 1/1\n📌 財經\n\n英央行維持利率 3.75%，行長警告通膨壓力仍在\n\n英國央行（Bank of England）宣布維持利率在 3.75%，按兵不動。上次降息是去年十二月，此後中東戰事推高了能源成本。行長 Andrew Bailey 表示，雖然美伊已簽停火協議且油價稍降，通膨壓力「仍在管道裡」，今年英國民眾要多花一點錢。\n\n—— 本則整理自 BBC、The Guardian 與 The New York Times 於 2026 年 6 月 18 至 19 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "英國央行（Bank of England）宣布利率維持在 3.75%，不做調整。上一次降息在去年十二月，此後中東戰事推高了能源價格，使進一步降息難以落實。行長 Andrew Bailey 表示，雖然美國和伊朗已簽署初步停火協議且油價有所回落，但通膨壓力「仍在管道裡」，今年英國民眾預期將面對更高的生活成本。\n\n本則整理自 BBC、The Guardian 與 The New York Times 於 2026 年 6 月 18 至 19 日發佈的報導。",
    "voice_text": "英國央行（Bank of England）這次按兵不動，維持利率在 3.75%。上一次降息是去年十二月——之後中東局勢讓能源成本一路走高，降息計畫跟著停下來。雖然美伊剛簽了停火協議、油價稍微回落，行長 Andrew Bailey 還是說，通膨的壓力「還在管道裡」。今年英國民眾得做好多花一點錢的準備。",
    "confidence": "high", "opinion_level": "none",
    "claim_trace": [
        {"claim": "英國央行維持利率 3.75% 不變，上次降息為去年十二月", "source_id": "bbc_business", "source_title": "Interest rates held as Bank warns of impact of high energy prices", "source_url": "https://www.bbc.com/news/articles/c33yzm5mdjpo?at_medium=RSS&at_campaign=rss", "support_type": "direct"},
        {"claim": "Andrew Bailey 警告通膨壓力仍在，英國民眾今年預期面對更高成本", "source_id": "guardian_business", "source_title": "Bank of England governor warns UK public to expect higher costs this year", "source_url": "https://www.theguardian.com/business/2026/jun/18/interest-rates-bank-of-england-hold-keep-iran", "support_type": "direct"},
        {"claim": "英國官員警告即使美伊協議通膨仍將延續", "source_id": "nyt_business", "source_title": "Inflation Will Linger Despite U.S.-Iran Deal, British Officials Warn", "source_url": "https://www.nytimes.com/2026/06/18/business/uk-inflation-bank-of-england.html", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_006"] = {
    "headline": "Warsh 首次例會利率按兵不動",
    "context": "美國聯準會（Federal Reserve）新任主席 Kevin Warsh 主持第一次例行利率會議，維持利率在 3.5% 至 3.75% 區間，但內部委員對今年是否升息存在分歧；Warsh 同時宣布將審查聯準會的運作方式。",
    "thread_text": "🧵 1/1\n📌 財經\n\nFed 首次由 Warsh 主持，利率維持不變\n\n新任聯準會（Federal Reserve）主席 Kevin Warsh 主持了他的第一次例行利率例會，決定維持聯邦基金利率在 3.5% 至 3.75% 區間。內部有委員認為今年可能需要升息一次以上。Warsh 同時宣布將審查聯準會的運作方式本身。\n\n—— 本則整理自 BBC 與 The New York Times 於 2026 年 6 月 17 至 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "聯準會（Federal Reserve）新任主席 Kevin Warsh 主持了他上任後的第一次利率例會，決定將利率維持在 3.5% 至 3.75% 區間，不做調整。但內部存在分歧：部分委員認為今年需要升息一次以上，立場偏向鷹派。Warsh 也宣布將啟動對聯準會自身運作方式的審查。\n\n本則整理自 BBC 與 The New York Times 於 2026 年 6 月 17 至 18 日發佈的報導。",
    "voice_text": "Kevin Warsh 主持聯準會（Federal Reserve）第一次例會，利率按兵不動，維持在 3.5% 到 3.75% 之間。這個「不動」背後不是沒有分歧——委員會裡有人認為今年可能需要升息一次以上。Warsh 還宣布要檢討聯準會的運作方式。他被外界形容為鷹派立場，這讓市場對利率走向的預測出現了新的變數。",
    "confidence": "high", "opinion_level": "none",
    "claim_trace": [
        {"claim": "Warsh 主持第一次例會，聯準會維持利率 3.5%-3.75%", "source_id": "bbc_business", "source_title": "Warsh to review how Fed works after holding US interest rates at first meeting", "source_url": "https://www.bbc.com/news/articles/cdjkl78vd7lo?at_medium=RSS&at_campaign=rss", "support_type": "direct"},
        {"claim": "聯準會委員對今年是否升息存在分歧", "source_id": "nyt_business", "source_title": "Fed holds rates steady at Warsh's first meeting.", "source_url": "https://www.nytimes.com/live/2026/06/17/business/fed-meeting-warsh-interest-rates/fed-holds-rates-steady-at-warshs-first-meeting", "support_type": "direct"}
    ]
}
REWRITES["daily_20260619_evt_024"] = {
    "headline": "鷹派聯準會引發債市拋售",
    "context": "聯準會新主席 Warsh 首次例會展現鷹派立場，市場預期利率可能長時間維持高檔，引發債券市場拋售潮。",
    "thread_text": "🧵 1/1\n📌 財經\n\nWarsh 鷹派轉向引爆債市拋售\n\n聯準會（Federal Reserve）主席 Kevin Warsh 首次主持例行利率例會後，市場解讀其立場偏鷹派，債券市場出現拋售潮。\n\n—— 本則來自 Reuters 於 2026 年 6 月 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "聯準會（Federal Reserve）新任主席 Kevin Warsh 首次主持利率例會後，市場解讀他的立場偏向鷹派，債券市場出現明顯拋售，引發所謂「債市潰跌（bond-market rout）」。\n\n本則來自 Reuters 於 2026 年 6 月 18 日發佈的報導。",
    "voice_text": "目前的消息指出，聯準會（Federal Reserve）的鷹派轉向開始衝擊債券市場。Warsh 主持第一次例會後，市場預期利率可能更長時間維持高位，引發了一波債市拋售。",
    "confidence": "medium", "opinion_level": "none",
    "claim_trace": [{"claim": "Warsh 鷹派立場引發債市拋售潮", "source_id": "reuters_business_google_news", "source_title": "Instant View: Fed holds steady in Warsh's debut, but hawkish shift fuels bond-market rout - Reuters", "source_url": "https://news.google.com/rss/articles/CBMiqgFBVV95cUxPaXdKWGRzWFlvOXVCQWxpMnZtNk1PcVBFU3BGbFZNaS1keXY1NGRGY2Y4blE4RGMzUXJTd0hSbS1kNllkWjBwLWNjenQ0VWhYVVcyTy04SjhkZ2lWbkstX1JOQ1F3UV8wMVQtMENxU01TbEdmQXBJanl3Q2ZZYjBCeVZ0ZnJIdTJJQkkyamJaWVI5c19VTTJIaUExeWsxb3dHUnl4M0h2YWg3Zw?oc=5", "support_type": "direct"}]
}
REWRITES["daily_20260619_evt_034"] = {
    "headline": "升息預期壓頂，華爾街下跌",
    "context": "市場押注聯準會今年可能升息，讓華爾街股市承壓下行。",
    "thread_text": "🧵 1/1\n📌 財經\n\n升息預期壓頂，華爾街走低\n\n市場對聯準會（Federal Reserve）今年可能升息的預期，讓華爾街（Wall Street）股市承壓，出現下跌走勢。\n\n—— 本則來自 Reuters 於 2026 年 6 月 18 日發佈的報導，讓圖書館員翻譯給你聽。",
    "threads_text": "市場開始押注聯準會（Federal Reserve）今年可能升息，這個預期讓華爾街（Wall Street）股市受壓，出現下跌走勢。\n\n本則來自 Reuters 於 2026 年 6 月 18 日發佈的報導。",
    "voice_text": "美股承壓。市場預期聯準會今年可能升息，這個判斷壓低了華爾街（Wall Street）的情緒，股市應聲走低。目前的消息指出，這波跌勢和聯準會的鷹派信號直接相關。",
    "confidence": "medium", "opinion_level": "none",
    "claim_trace": [{"claim": "市場押注聯準會今年升息，華爾街股市下跌", "source_id": "reuters_business_google_news", "source_title": "Wall Street sinks on bets Fed will hike rates this year - Reuters", "source_url": "https://news.google.com/rss/articles/CBMikwFBVV95cUxNUklQakNqNVVPRDVvUllkUHFYYVB4SXZTX3VkWml5eXJBRlJsZU4tclpReXJYc0dMTXhHaV9ySEtvTUpqbWhUcmI2YWM3THlWV1ZuUFpraFBTRldqUGJnZUN4ckRTV1BFc0NoZ0MwcDlPM1FQNE9sOVlyWjZLUFpDd0NxX1dYel9DMXltRmxjLTBvX2c?oc=5", "support_type": "direct"}]
}

FIELDS_TO_UPDATE = ["headline", "context", "thread_text", "threads_text", "voice_text", "confidence", "opinion_level", "claim_trace"]

updated = 0
skipped = 0
for event_id, rewrite in REWRITES.items():
    path = EVENTS_DIR / f"{event_id}.json"
    if not path.exists():
        print(f"SKIP {event_id}: file not found")
        skipped += 1
        continue
    data = json.loads(path.read_text())
    for field in FIELDS_TO_UPDATE:
        if field in rewrite:
            data[field] = rewrite[field]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"OK   {event_id}")
    updated += 1

print(f"\nDone: {updated} updated, {skipped} skipped")
