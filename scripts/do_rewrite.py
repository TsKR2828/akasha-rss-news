"""Step 2 rewrite — writes rewritten fields into event JSONs."""
import json, pathlib

DATE = "2026-06-18"
EVT_DIR = pathlib.Path(f"data/events/{DATE}")

REWRITES = {
"daily_20260618_evt_241": {
  "headline": "魯拉警告川普勿干預選舉",
  "context": "巴西總統魯拉（Luiz Inácio Lula da Silva）公開要求川普不要干預巴西選舉，說得很直接：「別多管閒事。」他目前正在爭取連任，對手是右翼候選人弗拉維歐・波索納洛（Flavio Bolsonaro），後者是川普的政治盟友。",
  "thread_text": "魯拉警告川普勿干預選舉\n\n巴西總統魯拉（Luiz Inácio Lula da Silva）直接要求川普不要插手巴西的選舉。這話背後有脈絡：他眼下正以些微差距對陣右翼候選人弗拉維歐・波索納洛（Flavio Bolsonaro），後者是川普的政治盟友。\n\n—— 本則整理自 Reuters 與 Al Jazeera，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "魯拉警告川普勿干預選舉\n\n巴西總統魯拉（Luiz Inácio Lula da Silva）公開要求川普不要干預巴西選舉。他說得很直接：「不准多管閒事。」\n\n眼前的背景是：魯拉正在以微弱差距對陣右翼候選人弗拉維歐・波索納洛（Flavio Bolsonaro）。這位候選人的父親是前總統波索納洛，也是川普在巴西最知名的政治盟友。\n\n本則整理自 Reuters 與 Al Jazeera 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "魯拉要川普別插手巴西選舉。巴西總統魯拉最近說得很明白——川普，別多管閒事。他目前正在爭取連任，對手是右翼候選人弗拉維歐・波索納洛（Flavio Bolsonaro），這位候選人的父親正是前總統波索納洛，也是川普的政治盟友。這場選舉本來就很緊，外部勢力的動向讓局勢更添一層變數。",
  "confidence": "high",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "魯拉公開要求川普不干預巴西選舉", "source_id": "reuters_world_google_news", "source_title": "Lula says Trump must 'stay out' of Brazil elections - Reuters", "source_url": "https://news.google.com/rss/articles/CBMingFBVV95cUxQQ0F1dC1KTFdQMlIwY25kMm9LQ1RuUzlzOEdFSWlLX0p5T3NvNzRqUl9iYV82NDFtY3Z0WkV3dUFrNDNOcXJmUTE3VnUzR3lSdy1weGxYaDlFSl80WkduaFNDdnZGNlNwRlI5eVBkanVKNHJsd2hWQ1NvUWFOX2ZzTWZmWXM3WTQxZFB6RmVjWndNX2lKWmdEdkRZYnVCZw?oc=5", "support_type": "direct"},
    {"claim": "魯拉正對陣右翼候選人弗拉維歐・波索納洛（川普盟友）", "source_id": "aljazeera_all", "source_title": "'Don't meddle': Lula calls on Trump to stay out of Brazil's elections", "source_url": "https://www.aljazeera.com/news/2026/6/17/dont-meddle-lula-calls-on-trump-to-stay-out-of-brazils-elections?traffic_source=rss", "support_type": "direct"}
  ]
},
"daily_20260618_evt_028": {
  "headline": "美軍擊毀疑似毒品走私船",
  "context": "美軍在東太平洋對一艘疑似走私毒品的船隻發動攻擊，造成 1 人死亡、2 人生還。這是美軍在類似行動中累計的第 208 個確認死亡案例。",
  "thread_text": "美軍擊毀疑似毒品走私船\n\n美軍在東太平洋擊沉一艘疑似走私毒品的船隻，1 人死亡、2 人生還。目前的消息指出，這已是美軍在類似行動中第 208 個確認死亡案例。\n\n—— 本則整理自 Reuters 與 NPR，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "美軍擊毀疑似毒品走私船\n\n美軍在東太平洋對一艘疑似走私毒品的船隻發動攻擊，1 人在行動中死亡，2 人生還。\n\n這件事有個數字背景：此次死亡是美軍執行類似船隻攻擊行動以來，累計的第 208 條人命。\n\n本則整理自 Reuters 與 NPR 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "美軍在東太平洋擊沉了一艘疑似走私毒品的船。1 人死亡，2 人生還。這件事有個數字背景：這次的死亡，是美軍執行類似行動以來累計的第 208 個確認死亡案例。",
  "confidence": "high",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "美軍在東太平洋擊沉疑似毒品船，1死2生還", "source_id": "reuters_world_google_news", "source_title": "US military says one killed, two survive in its strike on vessel in Eastern Pacific - Reuters", "source_url": "https://news.google.com/rss/articles/CBMitgFBVV95cUxNY0U1TTR0RmZQdUJiaUQ0c0g1dW5xR1lpYjVWMXZaN3V2d2NNbWMzNXpOb0IwV2ZrNmpzVS1uR2FRbmhxbFVrNkxVdmdsNkNrMUR2MmJuVXpaSElrM1ZHdzhUN0dFdEJXaXNFRklhcHRhSUhhZWcxTFRIbG53R2R0YWtEUC1ycXRsM3c1bUQ1SlNBcDQ1MEo5WVNudm5BbEY2UDJNWGJpSlhzT3lva0wxVE9Wb2djZw?oc=5", "support_type": "direct"},
    {"claim": "此為美軍類似行動累計第208個死亡案例", "source_id": "npr_world", "source_title": "U.S. strike on an alleged drug boat kills 1, leaves 2 survivors", "source_url": "https://www.npr.org/2026/06/17/nx-s1-5861424/u-s-strike-drug-boat-survivors", "support_type": "direct"}
  ]
},
"daily_20260618_evt_186": {
  "headline": "曼吉歐尼案採精神狀態抗辯",
  "context": "涉嫌刺殺美國健保巨頭 UnitedHealth 執行長 Brian Thompson 的路易吉・曼吉歐尼（Luigi Mangione），辯護律師宣布將在州立謀殺審判中主張「極端情緒紊亂」（extreme emotional disturbance）。若陪審團接受，量刑將會較輕。",
  "thread_text": "曼吉歐尼案採精神狀態抗辯\n\n涉嫌殺害 UnitedHealth 執行長 Brian Thompson 的路易吉・曼吉歐尼（Luigi Mangione），辯護律師宣布將在審判中主張「極端情緒紊亂」（extreme emotional disturbance）。若陪審團接受這項主張，他面臨的刑罰將比謀殺罪更輕。\n\n—— 本則整理自 BBC 與 Al Jazeera，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "曼吉歐尼案採精神狀態抗辯\n\n涉嫌刺殺美國健保巨頭 UnitedHealth 執行長 Brian Thompson 的路易吉・曼吉歐尼（Luigi Mangione），其辯護律師宣布將在州立謀殺審判中提出精神狀態抗辯——主張他行案當時處於「極端情緒紊亂」（extreme emotional disturbance）的狀態。\n\n若陪審團接受這項主張，曼吉歐尼面臨的刑罰將比謀殺罪名更輕。\n\n本則整理自 BBC 與 Al Jazeera 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "曼吉歐尼案有新進展。涉嫌刺殺美國健保巨頭 UnitedHealth 執行長 Brian Thompson 的路易吉・曼吉歐尼（Luigi Mangione），他的辯護律師準備在審判中採用精神狀態抗辯，主張他行案當時處於「極端情緒紊亂」的狀態。這個策略如果成立，量刑會比謀殺罪更輕。",
  "confidence": "high",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "曼吉歐尼律師將在審判中主張極端情緒紊亂", "source_id": "bbc_world", "source_title": "Mangione's lawyers plan psychiatric defence in state murder trial", "source_url": "https://www.bbc.com/news/articles/c1lym76jyymo?at_medium=RSS&at_campaign=rss", "support_type": "direct"},
    {"claim": "精神狀態抗辯若成立可獲較輕量刑", "source_id": "aljazeera_all", "source_title": "Luigi Mangione to use psychiatric defence in healthcare CEO murder case", "source_url": "https://www.aljazeera.com/news/2026/6/17/luigi-mangione-to-use-psychiatric-defence-in-healthcare-ceo-murder-case?traffic_source=rss", "support_type": "direct"}
  ]
},
"daily_20260618_evt_019": {
  "headline": "波索納洛之子遭巴西法院定罪",
  "context": "巴西法院裁定前總統賈伊・波索納洛（Jair Bolsonaro）之子埃杜阿爾多・波索納洛（Eduardo Bolsonaro）有罪，指其曾向美國尋求協助，試圖影響父親的司法訴訟走向。埃杜阿爾多強烈否認，稱定罪「毫無根據且荒謬」。",
  "thread_text": "波索納洛之子遭巴西法院定罪\n\n巴西法院裁定前總統波索納洛（Jair Bolsonaro）之子埃杜阿爾多（Eduardo Bolsonaro）有罪——他被指控曾向美國尋求幫助，試圖影響父親的司法訴訟走向。埃杜阿爾多否認，稱定罪「毫無根據且荒謬」。\n\n—— 本則整理自 Reuters 與 BBC，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "波索納洛之子遭巴西法院定罪\n\n巴西法院裁定前總統賈伊・波索納洛（Jair Bolsonaro）之子埃杜阿爾多（Eduardo Bolsonaro）有罪，指控他曾私下向美國尋求協助，企圖影響父親的司法訴訟走向。\n\n埃杜阿爾多強烈否認，稱定罪「毫無根據且荒謬」。\n\n本則整理自 Reuters 與 BBC 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "巴西對前總統波索納洛的兒子下了定罪判決。埃杜阿爾多・波索納洛（Eduardo Bolsonaro）被裁定有罪，理由是他曾向美國尋求幫助，企圖影響父親賈伊・波索納洛（Jair Bolsonaro）的司法訴訟。埃杜阿爾多否認，說定罪「毫無根據且荒謬」。",
  "confidence": "high",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "巴西法院裁定埃杜阿爾多・波索納洛有罪，罪名是向美國尋求協助影響父親訴訟", "source_id": "reuters_world_google_news", "source_title": "Brazilian court convicts Eduardo Bolsonaro of seeking US help in father's legal battle - Reuters", "source_url": "https://news.google.com/rss/articles/CBMixgFBVV95cUxQTDBTRExIalhtazhlV0h0QWFEek5KeFN0WEl4aXI4U1RNNWlDQU9PMUVuV0lTcW15Sjc4RGZheXI3QW9VS3lRLWtralhzQm9xWWsxQmMyMUwxM0o4R2VyZ29KNFJCTENWMnBIMEIwTHBKamdQMWVwVHJXQVpiQmxLcUxjQmNrZ1JYZEhWRndjdFgyaXpUNzVZVjFFcTVwcGduTVVnV21welJsTUpsWUdGRVpoaVlrMUZrTkd0a3pOYkJUbUFyNEE?oc=5", "support_type": "direct"},
    {"claim": "埃杜阿爾多稱定罪毫無根據且荒謬", "source_id": "bbc_world", "source_title": "Brazil convicts Jair Bolsonaro's son of pursuing US help in father's legal battle", "source_url": "https://www.bbc.com/news/articles/cgl3x0pey9lo?at_medium=RSS&at_campaign=rss", "support_type": "direct"}
  ]
},
"daily_20260618_evt_089": {
  "headline": "挪威王儲妃肺臟移植成功",
  "context": "挪威王儲妃梅特-瑪麗特（Crown Princess Mette-Marit）完成肺臟移植手術，王室確認手術順利。她長期患有肺部纖維化（pulmonary fibrosis），術後需在醫院休養數週。",
  "thread_text": "挪威王儲妃肺臟移植成功\n\n挪威王儲妃梅特-瑪麗特（Crown Princess Mette-Marit）接受了肺臟移植手術，王室宣布手術順利。她長期患有肺部纖維化（pulmonary fibrosis），術後將在醫院休養數週。\n\n—— 本則整理自 Reuters 與 BBC，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "挪威王儲妃肺臟移植成功\n\n挪威王儲妃梅特-瑪麗特（Crown Princess Mette-Marit）接受了肺臟移植手術，王室宣布手術順利成功。她長期與肺部纖維化（pulmonary fibrosis）共存——這是一種造成肺組織逐漸硬化的慢性病。\n\n術後她將留在醫院休養數週。\n\n本則整理自 Reuters 與 BBC 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "挪威王儲妃梅特-瑪麗特完成了肺臟移植手術。王室宣布手術順利。她長年患有肺部纖維化（pulmonary fibrosis）——一種讓肺組織逐漸硬化的慢性病——術後需在醫院休養數週。",
  "confidence": "high",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "挪威王儲妃梅特-瑪麗特肺臟移植手術順利", "source_id": "reuters_world_google_news", "source_title": "Norway's crown princess undergoes successful lung transplant, palace says - Reuters", "source_url": "https://news.google.com/rss/articles/CBMivAFBVV95cUxOX2ZNbDQ2RzNpOU5ObFpMY0JYbDlyRmpqNnVXbnJsWlhUN0p4dC1xN1lGZFlYaGVMVzlDaVE0VDNpeHM0SmFuOXFVSlNfc1FoT2hBcnd3ZC00V1FkejdLYUhDVGU3QW10Qi1zX0ZSRW1aQnBST2Z3WnVSaHRPTk9JMkkyVlZnODVWbzFFVUVFamRDVzVZZ05iN1d2NWo2R3lJcURRN1ZwWjMtSGpabE55SmdzeWFaLUtNWUtYag?oc=5", "support_type": "direct"},
    {"claim": "王儲妃患有肺部纖維化，術後將在醫院休養數週", "source_id": "bbc_world", "source_title": "Norway's crown princess undergoes successful lung transplant, palace says", "source_url": "https://www.bbc.com/news/articles/c1eyg37qyqjo?at_medium=RSS&at_campaign=rss", "support_type": "direct"}
  ]
},
"daily_20260618_evt_004": {
  "headline": "Gozney限量聯名披薩爐亮相",
  "context": "披薩爐品牌 Gozney 與油漆品牌 Tonester 攜手合作，推出限量聯名版「Tread」披薩爐，配色為暖棕色調「Car Coat」，由品牌創辦人親自設計。Dezeen 雜誌目前舉辦抽獎活動，提供一組完整聯名組合作為獎品。",
  "thread_text": "Gozney限量聯名披薩爐亮相\n\n披薩爐品牌 Gozney 與油漆品牌 Tonester 合作，推出限量版「Tread」披薩爐，配色是暖棕色調「Car Coat」——出自品牌創辦人的設計構想。目前有媒體舉辦抽獎，提供一組聯名組合的得獎機會。\n\n—— 本館報來自 Dezeen 設計媒體，2026 年 6 月 16 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "Gozney限量聯名披薩爐亮相\n\n披薩爐品牌 Gozney 與油漆品牌 Tonester 合作，聯手推出限量版「Tread」披薩爐，採暖棕色調「Car Coat」配色，靈感來自 Gozney 品牌創辦人的設計概念。\n\n目前有設計媒體舉辦抽獎，有機會贏得這款限量聯名組合。\n\n本館報來自 Dezeen 於 2026 年 6 月 16 日發佈的報導。",
  "voice_text": "設計圈這邊有個跨品牌合作。披薩爐品牌 Gozney 和油漆品牌 Tonester 合作，推出一款限量版「Tread」披薩爐，配色叫做「Car Coat」，是暖棕色調，靈感來自品牌創辦人的設計構想。目前有媒體舉辦抽獎，有機會獲得這款限量設計。",
  "confidence": "low",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "Gozney與Tonester合作推出限量版Tread披薩爐Car Coat配色", "source_id": "dezeen", "source_title": "Prize giveaway: win a Gozney Tread pizza oven bundle", "source_url": "https://www.dezeen.com/2026/06/16/prize-giveaway-gozney-pizza-oven-bundle-car-colour/", "support_type": "direct"}
  ]
},
"daily_20260618_evt_025": {
  "headline": "岩石庭院與浮葉亭水畔建築",
  "context": "中國上海滴水湖（Dishui Lake）西側，Atelier Z+ 建築事務所設計的兩棟建築「碎石庭院」（Clustered Rocks Court）與「浮葉亭」（Floating Leaf Pavilion）正式公開，分列黃日港河上黃樓橋的南北兩側，主要提供湖岸遊客餐飲服務，並作為公共活動核心節點。",
  "thread_text": "岩石庭院與浮葉亭水畔建築\n\n中國上海滴水湖（Dishui Lake）西側，Atelier Z+ 設計兩棟新建築：「碎石庭院」（Clustered Rocks Court）與「浮葉亭」（Floating Leaf Pavilion），分坐落黃樓橋南北兩岸，以餐飲服務為主，兼作湖岸公共活動據點。\n\n—— 本館報來自 ArchDaily，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "岩石庭院與浮葉亭水畔建築\n\n中國上海滴水湖（Dishui Lake）西側，由 Atelier Z+ 設計的兩棟建築「碎石庭院」（Clustered Rocks Court）與「浮葉亭」（Floating Leaf Pavilion）正式公開，分別座落在黃日港河上黃樓橋的南北兩側。\n\n兩棟建築以提供餐飲服務為主要功能，同時作為湖岸帶的公共活動核心節點。\n\n本館報來自 ArchDaily 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "建築這邊有一個中國新作品。上海滴水湖西側，由 Atelier Z+ 設計的「碎石庭院」和「浮葉亭」兩棟建築剛剛公開，座落在同一座橋的南北兩側。這兩棟建築主要提供餐飲服務，也是湖岸公共活動的據點。",
  "confidence": "medium",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "Atelier Z+設計碎石庭院與浮葉亭，位於上海滴水湖西側黃樓橋兩岸", "source_id": "archdaily", "source_title": "Clustered Rocks Court & Floating Leaf Pavilion / Atelier Z+", "source_url": "https://www.archdaily.com/1042404/clustered-rocks-court-and-floating-leaf-pavilion-atelier-z-plus", "support_type": "direct"}
  ]
},
"daily_20260618_evt_032": {
  "headline": "廚電成建築元素的設計趨勢",
  "context": "廚房空間已從單純的功能場所演變為家庭日常生活的核心。當代廚房設計將電器設備整合為建築語言的一部分，從材料選擇、位置布局到視覺整合，都納入設計考量，讓廚電在空間中扮演儲存、展示與日常使用的複合角色。",
  "thread_text": "廚電成建築元素的設計趨勢\n\n廚房早就不只是做菜的地方了。當代廚房設計把冰箱、烤箱、洗碗機等家電當成建築元素來思考——材料、位置、視覺整合都是設計語言的一部分。從功能空間到生活核心，廚房的角色在設計上已徹底轉型。\n\n—— 本館報來自 ArchDaily，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "廚電成建築元素的設計趨勢\n\n廚房空間的定位正在改變。當代廚房不再只是料理的場所，而是日常生活與家庭互動的核心——電器設備的角色也隨之升級，從純粹的功能工具，成為空間設計語言的一部分。\n\n設計重點不只是廚具如何運作，而是材質、形態與空間之間的對話。\n\n本館報來自 ArchDaily 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "廚房的設計語言正在改變。電器——冰箱、烤箱、洗碗機——已經不只是功能工具，而是當代廚房建築設計的一部分。材料、位置、視覺整合都在設計討論的範疇裡。廚房從做飯的空間演變成家的核心，這件事在設計圈已是顯學。",
  "confidence": "medium",
  "opinion_level": "light_context",
  "claim_trace": [
    {"claim": "當代廚房設計趨勢將電器整合為建築元素", "source_id": "archdaily", "source_title": "Appliances as Architectural Elements: Designing the Contemporary Kitchen", "source_url": "https://www.archdaily.com/1042318/appliances-as-architectural-elements-designing-the-contemporary-kitchen", "support_type": "direct"}
  ]
},
"daily_20260618_evt_003": {
  "headline": "ChatGPT不當圖片爭議觸發安全討論",
  "context": "有特定提示語（prompt）觸發 ChatGPT 生成令人不安的圖片，這件事引出外界對生成式 AI 內容安全邊界與審核機制的討論。目前消息來自單一來源，細節有限。",
  "thread_text": "ChatGPT不當圖片爭議觸發安全討論\n\n有人找到了一個特定提示語（prompt），能讓 ChatGPT 生成令人不安的圖片。這件事引出了更大的問題：生成式 AI 的安全邊界在哪裡，審核機制又走得多遠。目前的消息指出這是業界正在討論的焦點議題。\n\n—— 本館報來自 BBC 科技報導，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "ChatGPT不當圖片爭議觸發安全討論\n\n有人找到了一個特定提示語（prompt），能觸發 ChatGPT 生成令人不安的圖片。這件事引起了對生成式 AI 的安全機制討論：內容邊界應該劃在哪裡？審核系統又有多可靠？\n\n目前的消息有限，細節仍待確認。\n\n本館報來自 BBC 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "AI 安全這邊有個討論。有人找到了一個特定的提示語，能讓 ChatGPT 生成令人不安的圖片——這件事讓外界重新審視生成式 AI 的內容安全邊界。目前的消息有限，這個觸發點已引發業界對審核機制的討論。",
  "confidence": "medium",
  "opinion_level": "light_context",
  "claim_trace": [
    {"claim": "特定prompt可觸發ChatGPT生成令人不安的圖片", "source_id": "bbc_technology", "source_title": "Tech Life", "source_url": "https://www.bbc.co.uk/sounds/play/w3ct8jy0?at_medium=RSS&at_campaign=rss", "support_type": "direct"}
  ]
},
"daily_20260618_evt_001": {
  "headline": "Android 17正式發布整合Gemini",
  "context": "Google 正式發布 Android 17 與 Wear OS 7，帶來多工處理升級、家長控管強化、安全工具更新，以及智慧手錶端的新功能。同步推出的 Pixel Drop 將 Google 最新 AI 模型引入旗下裝置，Gemini 的整合範圍進一步擴大。",
  "thread_text": "Android 17正式發布整合Gemini\n\nGoogle 正式推出 Android 17 與 Wear OS 7，帶來多工處理升級、家長控管強化、安全工具更新，以及智慧手錶新功能。隨行的 Pixel Drop 把 Google 最新 AI 模型帶進旗下裝置——Gemini 的整合又往前推了一步。\n\n—— 本館報來自 TechCrunch，2026 年 6 月 16 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "Android 17正式發布整合Gemini\n\nGoogle 正式發布 Android 17 與 Wear OS 7，帶來包括多工處理升級、家長控管強化、安全工具更新，以及智慧手錶端的功能擴充。\n\n隨行推出的 Pixel Drop 進一步把 Google 最新的 AI 模型帶進旗下裝置，Gemini 的使用情境再擴大一步。\n\n本館報來自 TechCrunch 於 2026 年 6 月 16 日發佈的報導。",
  "voice_text": "Android 17 正式發布。Google 推出了新版 Android 17 和 Wear OS 7，帶來的功能包括多工處理升級、家長控管強化，還有智慧手錶的新功能。這次同步的 Pixel Drop 也讓 Google 最新的 AI 模型登上旗下裝置，Gemini 的整合範圍再擴大一步。",
  "confidence": "medium",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "Google發布Android 17與Wear OS 7，含多工、家長控管、安全功能及Pixel Drop", "source_id": "techcrunch_ai", "source_title": "Android 17 launches with new multitasking tools as Google expands Gemini features", "source_url": "https://techcrunch.com/2026/06/16/android-17-launches-with-new-multitasking-tools-as-google-expands-gemini-features/", "support_type": "direct"}
  ]
},
"daily_20260618_evt_196": {
  "headline": "Gemini接管Google智慧音箱",
  "context": "Google 推出全新 Google Home 智慧音箱，定價 99.99 美元（約新台幣 3,200 元），以 Gemini AI 取代原有的 Google Assistant，從固定指令模式轉向更自然的對話互動，試圖重新定義智慧音箱體驗。",
  "thread_text": "Gemini接管Google智慧音箱\n\nGoogle 推出全新 Google Home 智慧音箱，售價 99.99 美元。最大改變是拋棄 Google Assistant，改用 Gemini AI——從死板指令，轉向更自然的對話互動。目前的消息指出，這是 Google 試圖重新點燃智慧音箱產品線的一步。\n\n—— 本館報來自 TechCrunch，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "Gemini接管Google智慧音箱\n\nGoogle 推出新款 Google Home 智慧音箱，定價 99.99 美元。最大的改變是用 Gemini AI 取代原有的 Google Assistant，從死板的語音指令模式，轉向更接近自然對話的互動方式。\n\n目前的消息指出，Google 想用生成式 AI 重新定義智慧音箱體驗。\n\n本館報來自 TechCrunch 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "Google 智慧音箱換上了 Gemini。新款 Google Home 售價 99.99 美元——約合新台幣 3,200 元——最大改變是以 Gemini AI 取代原本的 Google Assistant。不同於舊版的固定指令，Gemini 走的是更自然的對話模式。",
  "confidence": "medium",
  "opinion_level": "light_context",
  "claim_trace": [
    {"claim": "Google推出99.99美元Google Home智慧音箱，以Gemini取代Google Assistant", "source_id": "techcrunch_ai", "source_title": "Google bets on Gemini to reinvent the smart home speaker", "source_url": "https://techcrunch.com/2026/06/17/google-bets-on-gemini-to-reinvent-the-smart-home-speaker/", "support_type": "direct"}
  ]
},
"daily_20260618_evt_217": {
  "headline": "矽谷AI燒錢潮後ROI拉警報",
  "context": "「Tokenmaxxing」（追求 AI 使用量最大化）曾是矽谷今年最熱的企業風潮，CEOs 鼓勵員工把 AI 用到極限。然後帳單寄來了：Uber 傳出幾個月燒光全年 AI 預算，部分公司削減 Claude 授權，Meta 也關掉了內部 AI 排行榜。",
  "thread_text": "矽谷AI燒錢潮後ROI拉警報\n\n「Tokenmaxxing」曾是今年矽谷最熱的風潮——CEO 們鼓勵員工把 AI 用到極限。然後帳單寄來了。Uber 傳出幾個月內燒光全年 AI 預算，部分公司縮減 Claude 授權範圍，Meta 悄悄關掉了內部 AI 排行榜。目前的消息指出，企業對 AI 的 ROI 質疑聲浪正在擴散。\n\n—— 本館報來自 TechCrunch，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "矽谷AI燒錢潮後ROI拉警報\n\n「Tokenmaxxing」曾是矽谷今年最熱的企業文化——CEO 們鼓勵員工把 AI 工具用到極限，越多越好。然後帳單寄來了。\n\n傳出 Uber 在幾個月內就燒完了全年的 AI 預算，部分公司縮減了 Claude 的授權範圍，Meta 更悄悄關掉了內部的 AI 使用排行榜。企業對 AI 投資報酬率的質疑，開始浮上檯面。\n\n本館報來自 TechCrunch 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "矽谷 AI 燒錢浪潮開始退燒了。「Tokenmaxxing」——讓員工把 AI token 使用量推到最大化——曾是今年企業界最熱的風潮。帳單寄來後，故事急轉直下：Uber 傳出幾個月燒光全年 AI 預算，部分公司削減了 AI 授權，Meta 也關掉了內部的 AI 排行榜。企業現在開始認真算 AI 到底划不划算了。",
  "confidence": "medium",
  "opinion_level": "light_context",
  "claim_trace": [
    {"claim": "Tokenmaxxing風潮後Uber燒光年度AI預算、公司削減Claude授權、Meta關閉AI排行榜", "source_id": "techcrunch_ai", "source_title": "NEA's Tiffany Luck on AI IPOs, personal agents, and the ROI reckoning", "source_url": "https://techcrunch.com/podcast/neas-tiffany-luck-on-ai-ipos-personal-agents-and-the-roi-reckoning/", "support_type": "direct"}
  ]
},
"daily_20260618_evt_238": {
  "headline": "奈及利亞前石油部長英國獲判無罪",
  "context": "奈及利亞前石油部長蒂贊尼・艾利森-馬杜艾克（Diezani Alison-Madueke）在英國受賄審判中，被倫敦南華克刑事法院（Southwark Crown Court）陪審團裁定無罪，原本指控她收受石油大亨賄賂的所有罪名均不成立。",
  "thread_text": "奈及利亞前石油部長英國獲判無罪\n\n奈及利亞前石油部長蒂贊尼・艾利森-馬杜艾克（Diezani Alison-Madueke）在英國受賄審判中獲判無罪。倫敦南華克刑事法院（Southwark Crown Court）的陪審團裁定，原本指控她收受石油大亨賄賂的所有罪名均不成立。\n\n—— 本則整理自 Reuters 與 BBC，2026 年 6 月 18 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "奈及利亞前石油部長英國獲判無罪\n\n奈及利亞前石油部長蒂贊尼・艾利森-馬杜艾克（Diezani Alison-Madueke）在英國受賄審判中全身而退。倫敦南華克刑事法院（Southwark Crown Court）的陪審團裁定，她被指控收受石油大亨賄賂的所有罪名均不成立。\n\n本則整理自 Reuters 與 BBC 於 2026 年 6 月 18 日發佈的報導。",
  "voice_text": "財經這邊有一則法院判決。奈及利亞前石油部長蒂贊尼・艾利森-馬杜艾克（Diezani Alison-Madueke），在英國的受賄審判中被陪審團裁定無罪。她原本被指控收受石油大亨的賄賂，全部罪名最終都未能成立。",
  "confidence": "high",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "蒂贊尼・艾利森-馬杜艾克在英國受賄審判中獲判無罪", "source_id": "reuters_world_google_news", "source_title": "Nigeria's ex-oil minister Alison-Madueke cleared of all charges in UK corruption trial - Reuters", "source_url": "https://news.google.com/rss/articles/CBMixwFBVV95cUxOR0ZyMkVYQXltZnJSWDNab2NJb29PNHV2VDBidXlpdlF6YlExNEt0QkRfalp1Q2E1MTRsVkk1MTM2YjM1LV9JRi1SZVc4Y3VYYjNwSEZsR2lUdkNsZk5UVEtUNHVXcVA1bjlrN2hjbTA3WmRjUkdDSENTS1ZwOUhaV2daSFZ6N2FBano1a1k5dUFNS1QyYm1JU1hWcHlaSmpNbVVBbVRXSFBuWHNnWnhMMUY4ZDNvaVRVZ3lkTHFGY1NNcmcyM2hV?oc=5", "support_type": "direct"},
    {"claim": "陪審團裁定指控收受石油大亨賄賂的罪名均不成立", "source_id": "bbc_world", "source_title": "Ex-Nigeria oil minister cleared in UK bribery trial", "source_url": "https://www.bbc.com/news/articles/c872pwx4x2vo?at_medium=RSS&at_campaign=rss", "support_type": "direct"}
  ]
},
"daily_20260618_evt_009": {
  "headline": "嘉吉研究牛脂製巴西生質柴油",
  "context": "農業巨頭嘉吉（Cargill）正在評估以牛脂（beef tallow）取代大豆油，作為巴西生質柴油（biodiesel）原料的可行性。背景是美國關稅讓大豆油在巴西市場的競爭力下滑，業者需要替代方案。",
  "thread_text": "嘉吉研究牛脂製巴西生質柴油\n\n農業巨頭嘉吉（Cargill）正在研究以牛脂（beef tallow）作為巴西生質柴油原料的可行性。原因是美國關稅讓大豆油的成本競爭力下降，業者必須找替代方案。目前的消息指出這仍在評估階段。\n\n—— 本館報來自 Reuters 新聞，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "嘉吉研究牛脂製巴西生質柴油\n\n農業巨頭嘉吉（Cargill）正在評估以牛脂（beef tallow）取代大豆油，作為巴西生質柴油（biodiesel）的原料。背景是美國關稅讓大豆油的成本競爭力在這個市場下滑，業者需要找出替代方案。\n\n目前這項評估仍在進行中。\n\n本館報來自 Reuters 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "財經面有個農業原料的轉向。農業巨頭嘉吉（Cargill）目前在評估，是否要用牛脂取代大豆油，作為巴西生質柴油的原料。原因是美國關稅讓大豆油的競爭力在這個市場下滑了。這項評估目前仍在進行，還沒有定論。",
  "confidence": "medium",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "嘉吉正在評估牛脂作為巴西生質柴油原料，因應美國關稅導致大豆油競爭力下滑", "source_id": "reuters_business_google_news", "source_title": "Cargill studies beef tallow for Brazil biodiesel as US tariffs bite - Reuters", "source_url": "https://news.google.com/rss/articles/CBMisgFBVV95cUxNdnVLTDI2OU5GUGJCaWozR0RwQmhrbUt2YXgzTE9MeXpITDY2QTNwMmZ4N25XNzQ5RHZBd2Z1d2phMWxFX2dXZ1I5YTk2LUNtTFNZZG45SXVGZWliR0N0UFVfdkY4YVBBRVQ5N1dLd3RNa0VZd2k1SmdJVzZWbm43Qk5kXzhiNHZhb2JfbC04N090aFJuYmlUUUR0aHRLQ25ROEV2VkJ0WGE1Y2pycFliLV9n?oc=5", "support_type": "direct"}
  ]
},
"daily_20260618_evt_043": {
  "headline": "印度盧比持平等候Fed決策",
  "context": "聯準會（Fed）利率決策前，印度盧比（Rupee）幾乎維持平盤——油價帶動的升值支撐，與市場對美元的需求形成拉鋸，兩股力道相抵，匯率幾乎停在原地。",
  "thread_text": "印度盧比持平等候Fed決策\n\n聯準會（Fed）利率決策前，印度盧比幾乎維持平盤。油價反彈帶來的升值動力，與市場對美元的需求恰好形成拉鋸，兩股力道相抵之下，匯率幾乎沒動。市場的態度是：先等聯準會表態，再說。\n\n—— 本館報來自 Reuters 新聞，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "印度盧比持平等候Fed決策\n\n聯準會（Fed）利率決策前，印度盧比幾乎持平。油價反彈帶來的升值力道，與市場對美元的需求恰好相抵，匯率維持在原地。\n\n市場的態度很統一：先等聯準會開口，再說。\n\n本館報來自 Reuters 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "聯準會利率決策前，印度盧比幾乎沒動。油價帶動的漲勢和美元需求的壓力恰好相抵，匯率維持在平盤。市場在這個時間點的態度很統一：先等聯準會開口，再說。",
  "confidence": "medium",
  "opinion_level": "light_context",
  "claim_trace": [
    {"claim": "聯準會決策前印度盧比幾乎持平，油價與美元需求拉鋸", "source_id": "reuters_world_google_news", "source_title": "Rupee nearly flat as oil-led rally faces off against dollar demand; Fed verdict looms - Reuters", "source_url": "https://news.google.com/rss/articles/CBMisgFBVV95cUxNR1NCX29Fck41YWdHTTdRNXpOeE1Ca3BiTjM2RmNjQkMxb3VhVzVOeVgzRFNxNGZQb01MY2d2S3JxWTBaYXJkTHVhMEtSYVNyM3NwaV9fNldJTlhVQTZrVUwxTUZnT3VycVVsS09GU2lfOUFLZFlsTUlUb3hVMU90c3IzOW5pUUJQbWJJaUh5NE95VG9qVmJoUjF1clVtOEpxZ2tQX25lbkZZNVFvOUI4Rndn?oc=5", "support_type": "direct"}
  ]
},
"daily_20260618_evt_045": {
  "headline": "越南維持2026年GDP目標",
  "context": "越南政府宣布維持 2026 年 GDP 成長目標不變，儘管目前面臨貿易逆差擴大與通膨壓力上升的雙重挑戰。",
  "thread_text": "越南維持2026年GDP目標\n\n越南政府表示，儘管面臨貿易逆差擴大與通膨壓力，仍將維持 2026 年 GDP 成長目標。目前的消息指出這是越南政府的官方立場。\n\n—— 本館報來自 Reuters 新聞，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "越南維持2026年GDP目標\n\n越南政府宣布，儘管面臨貿易逆差擴大和通膨壓力雙重夾擊，仍將維持 2026 年的 GDP 成長目標不動搖。\n\n本館報來自 Reuters 於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "越南堅持今年的 GDP 目標。儘管面對貿易逆差擴大和通膨上升的雙重壓力，越南政府宣布仍維持 2026 年的經濟成長目標。",
  "confidence": "medium",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "越南維持2026年GDP目標，儘管面對貿易逆差與通膨壓力", "source_id": "reuters_world_google_news", "source_title": "Vietnam maintains 2026 GDP target despite trade deficit, inflation pressure - Reuters", "source_url": "https://news.google.com/rss/articles/CBMiyAFBVV95cUxPNEhWeFdoYl9XVlUyVjQxWE5UQ0xFbnZiajlyNG5ibzRQQmtCcHVCcnV5c3BDcHMtRUVTeUlKVkxuY1RtTFdPdlRndnN1eDlVdlpmbmE4dFgtZ1lKU2VkSVYwTXM3ZVNwQU5ITURUaW1Xd0tXTEpiR3ljakdFVTZUTl9WX2NadEhYSVVlcktxN3BsUjdmemxNVlE2andFbmJWSXBfclVVWDRSbnMwaUZnWDllQ3NDckthMTYyZHJjZE52MHpNODZaTg?oc=5", "support_type": "direct"}
  ]
},
"daily_20260618_evt_077": {
  "headline": "寬尾鳳蝶現身太平山請減速",
  "context": "台灣特有種「寬尾鳳蝶」每年 5 至 6 月進入活動高峰，近日已在宜蘭太平山國家森林遊樂區出現蹤跡，但也傳出路殺情形。林保署宜蘭分署呼籲行經太平山莊、鳩之澤等熱區的駕駛減速慢行，守護這隻「國寶蝶」。",
  "thread_text": "寬尾鳳蝶現身太平山請減速\n\n台灣特有種「寬尾鳳蝶」又到了每年 5、6 月的活動高峰。近日已在宜蘭太平山國家森林遊樂區現蹤，但也有民眾發現牠遭路殺。林保署呼籲行經太平山莊、鳩之澤等熱區的駕駛，請減速慢行、留意路旁動態，一起守護這隻「國寶蝶」。\n\n—— 本館報來自公視新聞，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "寬尾鳳蝶現身太平山請減速\n\n每年 5 到 6 月，是台灣特有種「寬尾鳳蝶」的主要活動季節。近日牠已在宜蘭太平山國家森林遊樂區出現，但也有民眾發現牠遭路殺。\n\n林保署宜蘭分署呼籲行經太平山莊、鳩之澤等常出沒路段的駕駛，請減速慢行，留意路面與路旁動態，共同守護這隻「國寶蝶」。\n\n本館報來自公視新聞於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "這個季節，寬尾鳳蝶出現了。台灣特有種的寬尾鳳蝶，每年 5 到 6 月是牠最活躍的時候，近日已在宜蘭太平山國家森林遊樂區看到蹤跡。不過也有民眾反映，牠在路上遭到輾壓。林保署呼籲行經太平山莊一帶的駕駛，請放慢速度、留意路旁動靜——這隻「國寶蝶」，需要我們一起守護。",
  "confidence": "medium",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "寬尾鳳蝶近日現身太平山國家森林遊樂區，傳出路殺情形，林保署呼籲減速", "source_id": "pts_news", "source_title": "台灣特有種寬尾鳳蝶太平山現蹤 林保署籲車輛減速防路殺", "source_url": "https://news.pts.org.tw/article/813418", "support_type": "direct"}
  ]
},
"daily_20260618_evt_079": {
  "headline": "G7聯合聲明重申台海現狀立場",
  "context": "G7 七國峰會第二天，七國領袖聯合發表聲明，重申反對任何片面改變東海、南海及台灣海峽現狀的企圖，強調相關爭議應透過對話和平解決。聲明也涵蓋北韓無核化、阻止伊朗核武、持續對烏軍援及加強對俄制裁等議題。",
  "thread_text": "G7聯合聲明重申台海現狀立場\n\nG7 峰會第二天，七國領袖發表聯合聲明，重申反對任何片面改變東海、南海及台灣海峽現狀的企圖，強調相關爭議應以對話方式和平解決。聲明同時涵蓋北韓無核化、阻止伊朗核武，以及持續對烏軍援、加強對俄制裁。\n\n—— 本館報來自公視新聞，2026 年 6 月 17 日發佈，讓圖書館員翻譯給你聽。",
  "threads_text": "G7聯合聲明重申台海現狀立場\n\nG7 峰會第二天，七國領袖發表聯合聲明，重申反對任何片面改變東海、南海及台灣海峽現狀的企圖，強調相關爭議應以對話方式和平解決。\n\n聲明也涵蓋其他主要議題：推動北韓完全無核化、阻止伊朗取得核武，並承諾持續擴大對烏克蘭的軍援、加強對俄羅斯的制裁。\n\n本館報來自公視新聞於 2026 年 6 月 17 日發佈的報導。",
  "voice_text": "G7 七國領袖在峰會第二天發表了聯合聲明。聲明重申反對任何片面改變東海、南海與台灣海峽現狀的企圖，相關爭議應透過對話和平解決。同時也提到北韓無核化、阻止伊朗核武，以及持續對烏克蘭軍援、加強對俄制裁。",
  "confidence": "medium",
  "opinion_level": "none",
  "claim_trace": [
    {"claim": "G7峰會聯合聲明反對片面改變台海及東南海現狀，呼籲對話解決", "source_id": "pts_news", "source_title": "G7峰會領袖發聯合聲明 重申反對任何片面改變台海現狀企圖", "source_url": "https://news.pts.org.tw/article/813419", "support_type": "direct"}
  ]
},
}

def update_event(event_id, rewrite):
    path = EVT_DIR / f"{event_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for k, v in rewrite.items():
        data[k] = v
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ {event_id}")

if __name__ == "__main__":
    print(f"Writing {len(REWRITES)} events to {EVT_DIR}/")
    for eid, rw in REWRITES.items():
        update_event(eid, rw)
    print("Done.")
