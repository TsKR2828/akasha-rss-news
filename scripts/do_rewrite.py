"""
Step 2 改寫腳本：依 rewrite_prompt.md 規則對 2026-06-13 選取事件進行繁中改寫。
由 agent 直接執行，不呼叫外部 API。
"""
import json, os, sys

DATE = "2026-06-13"
EVENTS_DIR = f"/home/user/akasha-rss-news/data/events/{DATE}"

# 每個 event 的改寫資料
# 鐵則：thread_text 純文字，無 emoji 標頭，無手動 1/N
REWRITES = {

"daily_20260613_evt_002": {
    "headline": "芝加哥設計週11件創意展品",
    "context": "今年芝加哥設計週（Chicago Design Week）在城市中心商品集市（Merchandise Mart）與 Fulton 街區同步展出。展品包括 Foster + Partners 工業設計部門以回收漁網製成的辦公椅，以及日本設計師深澤直人（Naoto Fukasawa）設計的輕量鋁製長椅。",
    "thread_text": (
        "芝加哥設計週11件創意展品\n\n"
        "今年的芝加哥設計週在 Merchandise Mart 與 Fulton 街區兩處同步展出。"
        "展品亮點有：Foster + Partners 工業設計部門用回收漁網做的辦公椅；"
        "深澤直人（Naoto Fukasawa）帶來輕量鋁製長椅。\n\n"
        "目前只有 Dezeen 一個來源報導此事，細節仍有限。\n\n"
        "—— 本則來自 Dezeen，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "芝加哥設計週11件創意展品\n\n"
        "今年芝加哥設計週（Chicago Design Week）在城市中心的 Merchandise Mart "
        "與 Fulton 街區同步展出。展品亮點包括：Foster + Partners 工業設計部門以回收漁網製成的辦公椅，"
        "以及日本設計師深澤直人（Naoto Fukasawa）設計的輕量鋁製長椅。\n\n"
        "本則來自 Dezeen 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "芝加哥設計週今年展出了十一件亮眼作品。"
        "Foster + Partners 工業設計部門做了一張用回收漁網製成的辦公椅；"
        "深澤直人帶來輕量鋁製長椅。\n\n"
        "兩個展區同步進行，一個在 Merchandise Mart，一個在 Fulton 街區。"
        "回收材料、輕量設計——這幾件作品代表了當代工業設計的一個重要方向。"
    ),
    "confidence": "low",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "Foster + Partners 以回收漁網製成辦公椅及深澤直人設計鋁製長椅，均於芝加哥設計週展出",
            "source_id": "dezeen",
            "source_title": "Eleven innovative collections from Chicago Design Week",
            "source_url": "https://www.dezeen.com/2026/06/11/chicago-design-week-neocon-2026-round-up/",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_003": {
    "headline": "英倫事務所操刀印度湖畔展亭",
    "context": "倫敦建築事務所 Studio Mango 在印度欽奈（Chennai）以南的海岸基地，完成了名為「四牆」（Four Walls）的湖畔展亭。這是一個新住宅開發案 Sanctuary by Aarth 的第一棟建築，兼作展廊與聚會空間，讓訪客一踏入就能望見基地核心的湖景。",
    "thread_text": (
        "英倫事務所操刀印度湖畔展亭\n\n"
        "倫敦建築事務所 Studio Mango 在印度欽奈（Chennai）南方的海岸基地，完成了「四牆」（Four Walls）展亭——"
        "新住宅開發案的第一棟建築，兼作展廊與聚會空間。\n\n"
        "設計的核心概念：讓訪客踏入第一步，就能望見整個基地所圍繞的那片湖。"
        "展亭是框架，湖才是主角。\n\n"
        "—— 本則來自 ArchDaily，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "英倫事務所操刀印度湖畔展亭\n\n"
        "倫敦建築事務所 Studio Mango 在印度欽奈（Chennai）以南的海岸基地，"
        "完成了名為「四牆」（Four Walls）的湖畔展亭。"
        "這是住宅開發案 Sanctuary by Aarth 的第一棟建築，設計簡潔，"
        "提供展廊與聚會空間，並讓訪客的第一視線直接落在基地核心的湖景上。\n\n"
        "本則來自 ArchDaily 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "Studio Mango 在印度欽奈以南，建了一座叫做「四牆」的湖畔展亭。"
        "它是整個住宅開發案的第一棟建築。\n\n"
        "展亭定位很特別——展廊和聚會空間都在這裡，但設計刻意保持簡潔，"
        "因為主角是湖，不是建築。"
        "造訪者一走進來，第一眼就會看見那片湖。"
    ),
    "confidence": "low",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "Studio Mango 完成印度欽奈南方海岸基地的湖畔展亭「四牆」",
            "source_id": "archdaily",
            "source_title": "Four Walls Pavilion / Studio Mango",
            "source_url": "https://www.archdaily.com/1042335/four-walls-pavilion-studio-mango",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_005": {
    "headline": "SpaceX上市SPV散戶恐難退出",
    "context": "SpaceX 完成 IPO 後，透過特殊目的載具（SPV，Special Purpose Vehicle）間接持股的小額投資人，恐將面臨隱藏費用、漫長等待期，甚至詐欺風險——他們要等到鎖定期解除，才能得知自己真正持有多少股份。",
    "thread_text": (
        "SpaceX上市SPV散戶恐難退出\n\n"
        "SpaceX IPO 完成了。但對那些透過 SPV（特殊目的載具）間接買進的小額投資人來說，"
        "故事才剛開始——而且不太美好。鎖定期解除前，他們甚至不知道自己究竟持有多少股。\n\n"
        "隱藏費用、漫長的等待，甚至詐欺風險。"
        "繞過公開市場投資熱門科技股的代價，現在到了算帳的時候。\n\n"
        "目前只有 TechCrunch 的報導，細節仍待確認。\n\n"
        "—— 本則來自 TechCrunch，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "SpaceX上市SPV散戶恐難退出\n\n"
        "SpaceX IPO 正式定案，但透過特殊目的載具（SPV）間接持股的小額投資人，"
        "可能要到上市後鎖定期解除，才能得知自己真正持有多少股份。\n\n"
        "目前報導指出，這類 SPV 的下層投資人面臨三重風險：隱藏費用、漫長等待期、以及詐欺的可能。"
        "繞過公開市場進入熱門科技股的代價，如今開始浮現。\n\n"
        "本則來自 TechCrunch 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "SpaceX 上市了，但有一群小額投資人現在面臨麻煩。"
        "他們當初透過特殊目的載具間接買進 SpaceX，"
        "直到鎖定期結束前，連自己真正持有多少股都不清楚。\n\n"
        "目前的消息指出，這類間接持股的小散戶，可能碰上三件事：隱藏費用、拿不到錢的漫長等待、以及詐欺風險。"
        "這就是繞過公開市場的代價。"
    ),
    "confidence": "medium",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "SpaceX IPO 後，透過 SPV 間接持股的小額投資人面臨鎖定期、隱藏費用及詐欺風險",
            "source_id": "techcrunch_ai",
            "source_title": "SpaceX SPV investors won't know their true holdings until post-IPO lock-ups lift",
            "source_url": "https://techcrunch.com/2026/06/11/spacex-spv-investors-wont-know-their-true-holdings-until-post-ipo-lock-ups-lift/",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_009": {
    "headline": "解析川普對伊戰略的矛盾訊號",
    "context": "BBC 記者 Gary O'Donoghue 分析了美國總統 Trump 在伊朗戰事期間前後矛盾的公開言論，以及這些混合訊號背後的可能意涵——究竟是政策搖擺，還是刻意製造模糊？這是一則評論性分析報導。",
    "thread_text": (
        "解析川普對伊戰略的矛盾訊號\n\n"
        "Trump 對伊朗戰事的說法，前後不一。BBC 記者 Gary O'Donoghue 試圖回答："
        "這是真的搖擺不定，還是刻意讓人摸不清底線的戰術？\n\n"
        "這是觀察與評論，不是新聞事件報導。"
        "但在這個節骨眼，讀懂白宮發出的訊號——或刻意製造的雜訊——"
        "可能和讀任何一份條約一樣重要。\n\n"
        "—— 本則來自 BBC，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "解析川普對伊戰略的矛盾訊號\n\n"
        "BBC 記者 Gary O'Donoghue 分析了美國總統 Trump 在伊朗戰爭期間的混合訊號："
        "時而強硬、時而緩和——究竟是政策尚未定錨，還是刻意讓對方捉摸不透？\n\n"
        "這是評論與分析，不是新聞事件報導。建議帶著自己的判斷去讀，而不是把它當作定論接收。\n\n"
        "本則來自 BBC 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "Trump 對伊朗戰事的說法，前後矛盾。一下強硬、一下緩和——這是立場搖擺，還是刻意的戰術？\n\n"
        "這則分析提出的問題比答案更多。"
        "在中東局勢緊繃的當下，理解華盛頓在說什麼、不說什麼，"
        "是判斷局勢走向的重要功課——但明確答案，目前我們還沒有。"
    ),
    "confidence": "medium",
    "opinion_level": "explicit_commentary",
    "claim_trace": [
        {
            "claim": "BBC 分析 Trump 在伊朗戰爭期間的混合訊號，提出「政策搖擺或刻意模糊」的疑問",
            "source_id": "bbc_world",
            "source_title": "Flip flop or deliberate? - Unpacking Trump's strategy on Iran",
            "source_url": "https://www.bbc.com/news/videos/cz9lg5ywzvpo?at_medium=RSS&at_campaign=rss",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_010": {
    "headline": "SpaceX正式定價史上最大IPO",
    "context": "SpaceX 宣布以每股 135 美元完成 IPO（首次公開募股）定價，正式啟動上市程序，成為有史以來規模最大的 IPO。",
    "thread_text": (
        "SpaceX正式定價史上最大IPO\n\n"
        "SpaceX 以每股 135 美元完成定價，正式啟動上市程序——據稱是有史以來規模最大的 IPO。\n\n"
        "Elon Musk 的火箭公司，終於從私人公司變成了你可以直接買股票的上市公司。"
        "規模多大？「史上最大」——這個說法目前只有 TechCrunch 一個來源，仍待更多確認。\n\n"
        "—— 本則來自 TechCrunch，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "SpaceX正式定價史上最大IPO\n\n"
        "SpaceX 宣布以每股 135 美元完成 IPO 定價，正式啟動上市程序，"
        "據報是有史以來規模最大的 IPO。\n\n"
        "Elon Musk 的火箭公司正式走向公開市場。"
        "目前定價消息已由 TechCrunch 確認，更多細節仍待進一步報導。\n\n"
        "本則來自 TechCrunch 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "SpaceX 定價了。每股 135 美元，據稱是有史以來規模最大的 IPO。\n\n"
        "Elon Musk 的火箭公司，正式成為上市公司。"
        "目前消息指出定價已確認，上市程序已啟動。"
        "「史上最大」這個說法仍有待更多來源驗證。"
    ),
    "confidence": "medium",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "SpaceX 以每股 135 美元完成 IPO 定價，規模據稱為史上最大",
            "source_id": "techcrunch_ai",
            "source_title": "SpaceX officially prices shares at $135 in the largest IPO ever",
            "source_url": "https://techcrunch.com/2026/06/11/spacex-officially-prices-shares-at-135-in-the-largest-ipo-ever/",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_016": {
    "headline": "上訴法院維持川普10%全球關稅",
    "context": "美國上訴法院延長了對下級法院裁決的「凍結」——該裁決原本認定 Trump 的 10% 全球關稅違法。凍結延長意味著關稅目前仍然有效，法律攻防繼續進行。",
    "thread_text": (
        "上訴法院維持川普10%全球關稅\n\n"
        "美國上訴法院延長了對下級法院裁決的暫緩執行——那個裁決原本要推翻 Trump 的 10% 全球關稅。"
        "現在的結果是：關稅繼續有效，法律攻防繼續進行。\n\n"
        "這是「暫時不推翻」，不是最終判決。"
        "法律戰還沒結束，只是關稅暫時沒有被撤銷。\n\n"
        "—— 本則來自 Reuters，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "上訴法院維持川普10%全球關稅\n\n"
        "美國上訴法院延長了對下級法院裁決的暫緩執行——原裁決認定 Trump 的 10% 全球關稅違法。"
        "這意味著關稅目前仍然有效，要等上訴法院作出最終裁決為止。\n\n"
        "這不是最終判決，只是法律程序的一個中間站。貿易政策的不確定性仍在繼續。\n\n"
        "本則來自 Reuters 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "川普的 10% 全球關稅，暫時繼續有效。"
        "上訴法院延長了對下級法院裁決的凍結——那個裁決本來要撤銷這項關稅。\n\n"
        "這不是最終答案。目前的意思是：法律還在打，關稅還沒被廢掉。"
        "後續上訴法院的正式裁決，才是真正的關鍵。"
    ),
    "confidence": "medium",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "美國上訴法院延長暫緩執行下級法院推翻 Trump 10% 全球關稅的裁決",
            "source_id": "reuters_world_google_news",
            "source_title": "US appeals court extends block on ruling against Trump's 10% global tariff - Reuters",
            "source_url": "https://news.google.com/rss/articles/CBMisAFBVV95cUxPUHJaZVVCYVVveXdhTDNMLWNhMG5hVlVPd2dFWXZTVHJzVFNhQ2V2RkdqWnE3dzRWR2RlbFZ0WmR6VnRLTVFiUmJ1NjdjZlgxbm43eHRfNjFZR2h4aTd5am1YRmhXbHBMbkZ3S3BtZFlzYzhlNG1sQ3pPN3VRUHFTcE14LUNPQWtFTmUyQ0VNRGdPM1ZQMzNjU1VZUHplMWZDelc0OGhWV2NJREhRVVpZMw?oc=5",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_030": {
    "headline": "Prometheus融資120億估值410億美元",
    "context": "Jeff Bezos 支持的 AI 新創 Prometheus 完成 120 億美元（約 1,200 億新台幣）融資，估值達 410 億美元（約 4,100 億新台幣）。公司目標是打造「人工通用工程師」（Artificial General Engineer），自動化重型工程作業與新藥設計。",
    "thread_text": (
        "Prometheus融資120億估值410億美元\n\n"
        "Jeff Bezos 支持的 AI 新創 Prometheus，完成了 120 億美元的新一輪融資，估值達 410 億美元。"
        "這家公司要打造的，是所謂「人工通用工程師」（Artificial General Engineer），"
        "目標是讓 AI 自動化重型工程和新藥設計。\n\n"
        "OpenAI 追求 AGI，Prometheus 要做的是「AGE」。名字不同，野心一樣驚人。"
        "目前只有 TechCrunch 的報導。\n\n"
        "—— 本則來自 TechCrunch，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "Prometheus融資120億估值410億美元\n\n"
        "Jeff Bezos 旗下的 AI 新創 Prometheus，完成 120 億美元（約 1,200 億新台幣）融資，"
        "估值達 410 億美元（約 4,100 億新台幣）。\n\n"
        "這家公司的核心概念是「人工通用工程師」（Artificial General Engineer），"
        "目標是用 AI 自動化重型工程專案與新藥設計——"
        "換句話說，讓機器來做工程師和製藥研究員的工作。\n\n"
        "本則來自 TechCrunch 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "Prometheus 完成了 120 億美元融資——大約 1,200 億新台幣。"
        "估值是 410 億美元，大概是 4,100 億台幣。"
        "這是 Jeff Bezos 支持的 AI 新創。\n\n"
        "這家公司的目標是打造「人工通用工程師」："
        "讓 AI 自動化重型工程作業和新藥設計。"
        "這跟追求通用人工智慧的路線不一樣——"
        "Prometheus 更聚焦在「做事」的 AI，而不只是「思考」的 AI。"
        "目前消息來自單一報導，仍待更多確認。"
    ),
    "confidence": "medium",
    "opinion_level": "light_context",
    "claim_trace": [
        {
            "claim": "Prometheus 完成 120 億美元融資，估值 410 億美元，目標打造「人工通用工程師」",
            "source_id": "techcrunch_ai",
            "source_title": "Jeff Bezos's Prometheus raises $12B to build an 'artificial general engineer' for the physical world",
            "source_url": "https://techcrunch.com/2026/06/11/jeff-bezoss-prometheus-raises-12b-to-build-an-artificial-general-engineer-for-the-physical-world/",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_031": {
    "headline": "韓銀行長：將適時調升利率",
    "context": "南韓央行（Bank of Korea）行長表示，利率將會「適時」調升。這一表態在全球貨幣政策走向備受矚目的當下，被市場解讀為升息方向已確立，但時間點仍有待觀察。",
    "thread_text": (
        "韓銀行長：將適時調升利率\n\n"
        "南韓央行行長表示，利率將「適時」調升。"
        "短短幾個字，但在全球貨幣政策走向備受矚目的當下，"
        "這代表南韓央行對升息方向已有共識。\n\n"
        "「適時」是很模糊的時間表。方向明確了：升。何時，還要等。\n\n"
        "—— 本則來自 Reuters，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "韓銀行長：將適時調升利率\n\n"
        "南韓央行（Bank of Korea）行長公開表示，利率將會「適時」調升。"
        "這番話在全球貨幣政策走向備受關注的當下，"
        "被市場解讀為升息方向已確立。\n\n"
        "「適時」預留了彈性，但方向已明確：利率將往上走。具體時機，仍待觀察。\n\n"
        "本則來自 Reuters 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "南韓央行行長說：利率將適時調升。方向明確，時間點還沒說死。\n\n"
        "在全球各國央行貨幣政策走向備受矚目的現在，"
        "這番話的意思很清楚——升息是遲早的事，"
        "只是「遲」還是「早」，南韓央行還沒給答案。"
    ),
    "confidence": "medium",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "南韓央行行長表示利率將「適時」調升",
            "source_id": "reuters_world_google_news",
            "source_title": "Bank of Korea governor says interest rates to be raised 'on time' - Reuters",
            "source_url": "https://news.google.com/rss/articles/CBMisgFBVV95cUxObUZzaEF5V1lIQzc3WS1EeEtOT0Z6d3ozS2RkTkRENmhoQkE0ek1LWHBwUE5CZVMyNUluNWd3bjBybjVQNE8tNzR4NkFMMFU4a3VGT19QaXNRTEQ4aXdQbVF2N1FhVGo3ME45S3FWc0JBQ0VqVGJSV0IzXzBYUUZsZFl5cHNoVFcwRksya2RTVUlQb0YyWUU1NXBZOFFqMkVTYm1pc0E4bFBVR0QwdmRrMkV3?oc=5",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_038": {
    "headline": "尹錫悅無人機案判刑30年",
    "context": "南韓前總統尹錫悅（Yoon Suk Yeol）及前國防部長，因被控於 2024 年命令無人機飛越平壤、藉此激化南北韓緊張、為宣布戒嚴製造藉口，今日遭法院各判刑 30 年。",
    "thread_text": (
        "尹錫悅無人機案判刑30年\n\n"
        "南韓前總統尹錫悅（Yoon Suk Yeol），今日遭法院以「操弄無人機飛越平壤煽動緊張、為戒嚴製造藉口」判刑三十年。"
        "前國防部長同獲三十年。\n\n"
        "2024 年底，尹錫悅突然宣布戒嚴，震驚全國。"
        "如今法院認定他刻意升高與北韓的緊張——無人機，是他給自己的「理由」。\n\n"
        "—— 本則來自 Reuters 與 NPR，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "尹錫悅無人機案判刑30年\n\n"
        "南韓前總統尹錫悅（Yoon Suk Yeol），今日遭法院判刑三十年。前國防部長同獲相同刑期。\n\n"
        "法院認定，尹錫悅命令於 2024 年派遣無人機飛越平壤，"
        "目的是製造與北韓的緊張情勢，進而替同年底的戒嚴宣布鋪路。"
        "這套操作，如今被法律正式定性。\n\n"
        "本則整理自 Reuters 與 NPR 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "南韓前總統尹錫悅，今天判刑三十年。前國防部長也是同樣的刑期。\n\n"
        "法院認定他在 2024 年底命令無人機飛越平壤，藉此激化南北韓緊張、"
        "替自己宣布戒嚴找理由。戒嚴那一晚震驚了整個南韓。"
        "如今，那個決定的代價是三十年。"
    ),
    "confidence": "high",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "南韓法院判尹錫悅及前國防部長各三十年，罪名為命令無人機飛越平壤並藉此為戒嚴製造藉口",
            "source_id": "reuters_world_google_news",
            "source_title": "South Korea court sentences ex-President Yoon to 30-year jail term over drone incursion - Reuters",
            "source_url": "https://news.google.com/rss/articles/CBMiyAFBVV95cUxOQW4ycGpINUt3YmRLOTZyakJhTUFJdWplMkhheFJLRXRJSHBVU1lDMmJhZHJJWXBST3dEVnRKcndJRXY3RUVZeUM1bDM1ZEdRTHpKekl1R3V5N0hSYzB0dWZNbkJScDFlbzZNMDdGeWRwY2R1UjFQN3JOQ0FUZGtuMUhsc3RWNVJlYXVzX1I4cGU2YnFZYXdSdWYwbWc5YzJYV050Mm8yLXlFUFcwSmlQSzA4QlF6RlhHN215NHk4VTJqRURrMjRjaA?oc=5",
            "support_type": "direct"
        },
        {
            "claim": "尹錫悅被控於 2024 年命令無人機飛越平壤以緊張局勢為戒嚴提供正當性",
            "source_id": "npr_world",
            "source_title": "Ousted South Korean President Yoon given prison term for drone flights over Pyongyang",
            "source_url": "https://www.npr.org/2026/06/12/nx-s1-5856122/ousted-south-korean-president-yoon-prison-drone-flights-pyongyang",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_045": {
    "headline": "印度擬容許財政赤字擴至GDP4.8%",
    "context": "據彭博社（Bloomberg）報導，印度政府有意讓財政赤字佔 GDP 的比例擴大至 4.8%，顯示印度願意為擴大財政操作空間而接受更高的赤字水位。",
    "thread_text": (
        "印度擬容許財政赤字擴至GDP4.8%\n\n"
        "印度政府據報有意讓財政赤字佔 GDP 的比例擴至 4.8%。"
        "這是彭博社的報導，Reuters 隨即跟進確認。\n\n"
        "對長期致力財政整合的新興市場大國來說，這是一個值得留意的訊號——"
        "放寬赤字上限，代表政府有意增加支出或接受更高負債。"
        "至於背後的目的，目前消息尚不完整。\n\n"
        "—— 本則來自 Reuters，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "印度擬容許財政赤字擴至GDP4.8%\n\n"
        "根據彭博社報導，印度政府有意讓財政赤字佔 GDP 的比例擴大至 4.8%，Reuters 也跟進報導。\n\n"
        "對長期致力財政整合的印度來說，這是一個值得留意的方向轉變——"
        "意味著政府願意接受更高的負債水位，以換取更大的財政操作空間。\n\n"
        "本則來自 Reuters 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "印度據報有意讓財政赤字佔 GDP 的比例擴大至 4.8%。"
        "這個數字代表什麼？簡單說——印度政府願意借更多錢、花更多錢。\n\n"
        "目前這則消息來自彭博社，尚待印度官方正式說明。"
        "但對正在觀察新興市場的人來說，這是一個需要留意的政策訊號。"
    ),
    "confidence": "medium",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "印度政府據報有意讓財政赤字佔 GDP 比例擴大至 4.8%",
            "source_id": "reuters_world_google_news",
            "source_title": "India willing to let fiscal deficit widen to 4.8% of GDP, Bloomberg News reports - Reuters",
            "source_url": "https://news.google.com/rss/articles/CBMitwFBVV95cUxNN0swM2xrUGZOOUZNaGd6a0Z2bTh1dGY5T2dpVXVOZnctcEdZV2xyTkxzUXZwS3ptN215Wm85aUphLUtrN25QYVUtM1o5MWVuREEybXVPbGVnVnk0ZVJ0eFpLbVhiejk4NVp5U3VQSHlORnlBTTdDNjhzajVmbkxCM2EtNXJ5UHdhdkp1cHVMTkJSeG1kbzF6LS1DMXhiZ0Q3OGRhbE9XS2FvcjFYREY1QUV0dzVYQkk?oc=5",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_056": {
    "headline": "BIG操刀阿肯色州新STEM校園",
    "context": "丹麥建築事務所 BIG（Bjarke Ingels Group）獲選，設計美國阿肯色州本頓維爾（Bentonville）一所新 STEM 大學校園。校址位於沃爾瑪（Walmart）前總部舊址附近，校園面積約 3.9 萬平方公尺，涵蓋學術大樓、創客空間與學生宿舍，預計 2029 年迎接第一屆學生。",
    "thread_text": (
        "BIG操刀阿肯色州新STEM校園\n\n"
        "丹麥建築事務所 BIG（Bjarke Ingels Group）獲選，"
        "負責設計美國阿肯色州本頓維爾（Bentonville）的新 STEM 大學——"
        "地點就在沃爾瑪（Walmart）前總部旁邊。\n\n"
        "校園規模約 3.9 萬平方公尺，包含學術大樓、創客空間與學生宿舍，"
        "預計 2029 年開始招生。BIG 與 Polk Stanley Wilcox Architects 合作設計。\n\n"
        "—— 本則來自 ArchDaily，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "BIG操刀阿肯色州新STEM校園\n\n"
        "BIG（Bjarke Ingels Group）獲選，為美國阿肯色州本頓維爾設計一所新 STEM 大學。"
        "校址在沃爾瑪（Walmart）前總部附近，"
        "校園面積約 3.9 萬平方公尺（約 42.2 萬平方英尺），"
        "涵蓋學術大樓、創客空間與學生宿舍，目標是 2029 年開始招生。\n\n"
        "本則來自 ArchDaily 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "BIG 要在美國阿肯色州設計一所新大學校園。"
        "基地在本頓維爾，就在沃爾瑪前總部旁邊。\n\n"
        "校園規模約 3.9 萬平方公尺，有學術大樓、創客空間和學生宿舍。"
        "2029 年預計迎接第一屆學生。"
        "這是目前最新揭露的計畫，詳細設計細節還沒完全公開。"
    ),
    "confidence": "low",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "BIG 獲選設計阿肯色州本頓維爾 STEM 大學，面積約 3.9 萬平方公尺，2029 年開始招生",
            "source_id": "archdaily",
            "source_title": "BIG to Design Three-Building STEM University Campus in Arkansas, United States",
            "source_url": "https://www.archdaily.com/1042384/big-to-design-three-building-stem-university-campus-in-arkansas-united-states",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_080": {
    "headline": "中國拘捕美籍緬甸研究學者",
    "context": "中國當局以涉嫌「間諜活動、危害國家安全」為由，逮捕了美籍學者 Min Zin。他主持一個專注緬甸議題的智庫，在緬甸民主運動中也有長期活躍的背景。",
    "thread_text": (
        "中國拘捕美籍緬甸研究學者\n\n"
        "中國政府以「涉嫌間諜活動、危害國家安全」為由，逮捕了美籍學者 Min Zin。"
        "他是一個專注緬甸議題智庫的負責人，長年從事緬甸人權與民主倡議工作。\n\n"
        "近年中國對外籍人士祭出安全指控的案例有增多趨勢。"
        "Min Zin 曾是緬甸民主運動的活躍人士，這次拘捕也加深了外界對跨國鎮壓的疑慮。\n\n"
        "—— 本則來自 Reuters 與 NPR，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "中國拘捕美籍緬甸研究學者\n\n"
        "中國當局宣佈，以「涉嫌間諜活動、危害中國國家安全」為由，逮捕了美籍學者 Min Zin。"
        "他主持一個專注緬甸研究的智庫，在緬甸民主運動中也有長期活躍的背景。\n\n"
        "這類對外籍人士祭出安全指控的案例，近年在中國持續浮現，"
        "對於研究跨國鎮壓議題的觀察者來說，這次逮捕格外值得關注。\n\n"
        "本則整理自 Reuters 與 NPR 於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "中國逮捕了一名美籍學者。他叫 Min Zin，是一個專注緬甸議題智庫的負責人，"
        "曾是緬甸民主運動的活躍人士。\n\n"
        "中國當局給出的理由是涉嫌間諜活動、危害國家安全。"
        "這類針對外籍研究者的安全指控，近年在中國並不罕見——"
        "但每次都會讓國際社群繃緊神經。"
    ),
    "confidence": "high",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "中國以涉嫌間諜活動逮捕美籍緬甸研究學者 Min Zin",
            "source_id": "reuters_world_google_news",
            "source_title": "China arrests US scholar of Myanmar on suspicion of spying - Reuters",
            "source_url": "https://news.google.com/rss/articles/CBMingFBVV95cUxPeEdIUGN3OVpnUFo1b1hHTlhWSktoNmxZT1Vvc3FNNlZ0MGJWcDN1NnU2cTNYUGRXZWVzQllaNzFmaUJCOTdGRGw0VHJtYTJLMnhxQjVNdlpVTEpJVzhqa2p5M2QyblpXYXZxUXpWWFgxVjZfVUtfXzJLcG9XTUZ1X2tMZWx1MkYybFAwNTA2NVFFX1pIem1sM1k2eTBEdw?oc=5",
            "support_type": "direct"
        },
        {
            "claim": "Min Zin 主持專注緬甸議題智庫，被以「間諜活動危害中國國家安全」拘押",
            "source_id": "npr_world",
            "source_title": "China arrests a U.S. scholar with a history of Myanmar activism, suspected of spying",
            "source_url": "https://www.npr.org/2026/06/12/nx-s1-5856394/china-arrest-us-citizen-myanmar",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_082": {
    "headline": "吳乃仁欠台糖案裁定管收",
    "context": "民進黨前秘書長吳乃仁，因涉台糖土地案被判賠 1.7 億元，台糖聲請強制執行後拘提未果。昨（11 日）上午吳乃仁自行到台中地院，法院裁定管收，並解送台中看守所。全案仍可提起抗告。",
    "thread_text": (
        "吳乃仁欠台糖案裁定管收\n\n"
        "民進黨前秘書長吳乃仁，因涉台糖土地案被判賠 1.7 億元。"
        "日前遭拘提未果後，昨（11 日）上午自行到台中地院，"
        "法院隨即裁定管收，並送台中看守所。\n\n"
        "管收是民事強制執行的手段，用意在迫使債務人履行義務。"
        "此案台糖已聲請強制執行，吳乃仁仍可就管收裁定提起抗告。\n\n"
        "—— 本則來自公視，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "吳乃仁欠台糖案裁定管收\n\n"
        "民進黨前秘書長吳乃仁，因台糖土地案被判賠 1.7 億元，台糖聲請強制執行。"
        "日前吳乃仁遭拘提未果，昨（11 日）上午自行到台中地院報到，"
        "法院裁定管收，解送台中看守所。\n\n"
        "管收是民事強制執行手段，目的在迫使債務人履行賠償義務。全案仍可抗告。\n\n"
        "本則來自公視於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "吳乃仁昨天到台中地院，被法院裁定管收，已送台中看守所。\n\n"
        "這起案子的背景是台糖土地糾紛。"
        "法院先前判他賠 1.7 億元，台糖隨後聲請強制執行、申請拘提。"
        "管收是強制執行的手段之一，目的是要讓債務人履行賠償。"
        "全案還可以抗告，尚未定案。"
    ),
    "confidence": "medium",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "吳乃仁因台糖土地案判賠 1.7 億元，自行到台中地院後遭裁定管收送台中看守所",
            "source_id": "pts_news",
            "source_title": "欠台糖1.7億遭追討拘提 吳乃仁自行到案裁定管收",
            "source_url": "https://news.pts.org.tw/article/812770",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_086": {
    "headline": "日本熊害升溫今年已4死25人傷",
    "context": "日本今年熊害事件較 2025 年更為嚴重，全國已有 4 人死亡、9 個都道縣共 25 人遭野熊攻擊。福島市住宅區出現野熊傷人事件，追捕過程中熊疑似自行打開窗戶脫困、甚至打開水龍頭飲水，顯示野熊對都市環境的適應能力日益提升。",
    "thread_text": (
        "日本熊害升溫今年已4死25人傷\n\n"
        "日本今年的熊害事件比去年更嚴重。全國已有 4 人死亡，9 個都道縣共 25 人遭攻擊。\n\n"
        "福島市最近有一隻熊，在追捕過程中成功逃脫——"
        "還疑似自己打開窗戶逃走、甚至打開水龍頭喝水。"
        "日本野熊正在快速學習怎麼在城市裡生存，"
        "這讓人熊衝突的問題變得更難處理。\n\n"
        "—— 本則來自公視，2026 年 6 月 12 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "日本熊害升溫今年已4死25人傷\n\n"
        "日本今年熊害事件升溫，全國已有 4 人死亡，9 個都道縣共 25 人遭野熊攻擊，"
        "出沒頻率比 2025 年明顯增加。\n\n"
        "福島市近期的一起案例格外引人關注："
        "警方與獵人追捕一隻出現在住宅區的野熊，但這隻熊成功逃脫。"
        "根據現場痕跡，牠疑似自己打開窗戶離開，甚至可能打開水龍頭飲水。"
        "這些跡象顯示，日本野熊的都市適應能力正在快速提升。\n\n"
        "本則來自公視於 2026 年 6 月 12 日發佈的報導。"
    ),
    "voice_text": (
        "日本今年的熊害事件比去年更嚴重。"
        "目前全國已有 4 人死亡，9 個都道縣共 25 人遭到攻擊。\n\n"
        "最近福島市有一起案例讓大家特別在意："
        "一隻進入住宅區和工廠周邊的野熊，在追捕中成功逃脫。"
        "現場痕跡顯示，牠可能自己打開了窗戶、甚至打開水龍頭喝水。"
        "這種行為說明一件事：日本野熊正在快速學習怎麼在城市裡存活，"
        "這讓人熊衝突變得更難預防和處理。"
    ),
    "confidence": "medium",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "日本今年已有 4 人死亡、9 個都道縣 25 人遭野熊攻擊；福島市熊疑似打開窗戶脫困",
            "source_id": "pts_news",
            "source_title": "日熊害升溫今年全國已4死 9都道縣25人遭襲擊",
            "source_url": "https://news.pts.org.tw/article/812739",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_198": {
    "headline": "美伊和談文本協議達成",
    "context": "巴基斯坦總理謝里夫（Shehbaz Sharif）在 X 上宣稱，美國與伊朗的和平協議最終文本已達成共識，正商討後續步驟。Al Jazeera 也同步報導巴基斯坦試圖推動協議跨越終點線。文本確定不等於正式簽署。",
    "thread_text": (
        "美伊和談文本協議達成\n\n"
        "巴基斯坦總理謝里夫（Shehbaz Sharif）今日在 X 發文，"
        "宣稱美伊和平協議的最終文本已達共識，雙方目前正在商討後續步驟。\n\n"
        "巴基斯坦在這場談判中扮演中間人角色。"
        "文本協議不等於正式簽署——但如果屬實，"
        "這是中東局勢數週以來最明確的進展訊號。\n\n"
        "—— 本則來自 Reuters 與 Al Jazeera，2026 年 6 月 13 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "美伊和談文本協議達成\n\n"
        "巴基斯坦總理謝里夫（Shehbaz Sharif）今日在 X 平台發文，"
        "宣稱美國與伊朗的和平協議最終文本已達成共識，雙方正商討接下來的步驟。\n\n"
        "巴基斯坦近期在美伊談判中擔任要角。"
        "文本確定不代表協議正式生效，"
        "但對於持續數週的中東衝突來說，這是迄今最明確的外交訊號之一。\n\n"
        "本則整理自 Reuters 與 Al Jazeera 於 2026 年 6 月 13 日發佈的報導。"
    ),
    "voice_text": (
        "美伊和談可能出現重大突破。"
        "巴基斯坦總理今日宣稱，美國與伊朗的和平協議最終文本已達成共識，後續步驟正在商議中。\n\n"
        "巴基斯坦這段時間一直在兩方之間穿梭協調。"
        "文本確定並不等於正式簽署，"
        "但這是這場衝突啟動以來最明確的停戰訊號。"
    ),
    "confidence": "high",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "巴基斯坦總理謝里夫稱美伊和平協議最終文本已達共識，正商討後續步驟",
            "source_id": "reuters_world_google_news",
            "source_title": "Pakistan PM Sharif says in X post that final text of US-Iran peace deal agreed, working on next steps - Reuters",
            "source_url": "https://news.google.com/rss/articles/CBMi0AFBVV95cUxPTGh4dmxZZEUyaFBXVXFSTHlsMU9meXdHSW1tcFdGVU01Smt1d1dJckppTVVSeGNzQlVIZ0I2U0syZ2I1cHM4ZllnaWd4V21TS0FVc2I5UFdzTGdtNHU5LWtzV0swcm1KeUdrX0FKN1NWQWdvU3BYMWNMMmJrWnYxalBFdUcwWDk2UDJCN3ljbVRDd3NJVDBSN3JlY3djV1p0WldPRTdLYVJ3RDZDLUpvSXlTMWRlUHo2eEtpMkFKZXdieHdZRjlkaGhCNmVjamUx?oc=5",
            "support_type": "direct"
        },
        {
            "claim": "Al Jazeera 報導巴基斯坦正試圖推動美伊協議跨越終點線",
            "source_id": "aljazeera_all",
            "source_title": "Can Pakistan push the US-Iran deal over the finish line?",
            "source_url": "https://www.aljazeera.com/video/newsfeed/2026/6/12/can-pakistan-push-the-us-iran-deal-over-the-finish-line?traffic_source=rss",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_201": {
    "headline": "美伊和談預期帶動英股週漲油跌",
    "context": "美伊和平協議的可能性推動油價走低，市場預期中東衝突降溫將緩解能源供應壓力。受此影響，英國股市本週錄得周線上漲；與原油高度連動的加元，則因油價走弱延續本週跌勢。",
    "thread_text": (
        "美伊和談預期帶動英股週漲油跌\n\n"
        "美伊和談的希望正在影響市場。"
        "油價因「中東衝突可能結束」的預期而走低，"
        "帶動英國股市本週收漲；"
        "與原油高度連動的加元，則因油價下跌延續周線跌勢。\n\n"
        "市場先行——協議還沒正式簽，資金就已經開始重新布局了。\n\n"
        "—— 本則來自 Reuters，2026 年 6 月 13 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "美伊和談預期帶動英股週漲油跌\n\n"
        "美伊和平協議的可能性正在牽動金融市場。"
        "油價因中東衝突降溫預期而走低；英國股市受惠，本週錄得上漲；"
        "加元則因原油走弱，延續本週的跌勢。\n\n"
        "這是一個典型的「預期先行」故事——協議還沒正式簽，市場已經開始反應了。\n\n"
        "本則整理自 Reuters 於 2026 年 6 月 13 日發佈的報導。"
    ),
    "voice_text": (
        "美伊和談的希望，正在改變市場走向。"
        "油價下跌，因為大家預期中東衝突可能結束、能源供應壓力會減少。"
        "英國股市本週因此收漲；加元則因為跟原油高度連動，跟著走低。\n\n"
        "和談還沒正式定案，但金融市場已經在押注了。"
        "這種訊號先行、市場先動的模式，在重大外交事件前後很常見。"
    ),
    "confidence": "high",
    "opinion_level": "light_context",
    "claim_trace": [
        {
            "claim": "英國股市因美伊和談預期推動油價走低而本週收漲",
            "source_id": "reuters_world_google_news",
            "source_title": "UK shares clock weekly gains as Iran-US peace deal hopes push oil price lower - Reuters",
            "source_url": "https://news.google.com/rss/articles/CBMiqwFBVV95cUxNamdwTDgyZmlRUFFkSmMxWGlvRFAxSi04NnFtMXNhcnc4NVJld2tQYkNvOTlIdE5qTThkbzJ2WXlqVzFiX3VZampINS1FVlBMSkhRMXhncUplZHF2NGs0OXVOcFNDMF80S1BXT1lsbEEyQU1LLTdYU1VjemtqdHoxLXlBSjNNend6bk15aXlYOFNVblpKbGtfXzFGNm96eG5CeFN4b0hyd0xWQVE?oc=5",
            "support_type": "direct"
        },
        {
            "claim": "加元因中東和談預期油價走低而延續周線跌勢",
            "source_id": "reuters_business_google_news",
            "source_title": "Canadian dollar extends weekly decline as oil falls on Mideast peace deal hopes - Reuters",
            "source_url": "https://news.google.com/rss/articles/CBMiugFBVV95cUxOWVZpVU04WlEzQjRiakZCXzZENDJMUnpWMHo2MllEZVVHZklfOHRVQmJhWjJKaWZPNzNpVy11dEZfOWczUWxEQUZrS1EzcU13VnBMQjJGdjJoMko4aGI4cU5MQV9Hc3lZQUlkZmY2c2oybnVUREJIR283WVN3RzR5eWsxZ1cyRkdySzFjek1Tc3JmOFJCU3JJWTBBQWxxMVJLSUlkMjhWeDQ5amZVM2RlX1c1bWhiQU1GTnc?oc=5",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_203": {
    "headline": "馬斯克成全球首位兆億富翁",
    "context": "Tesla、SpaceX 與 X 的老闆 Elon Musk，如今成為全球有史以來第一位個人身價超過 1 兆美元（約新台幣 32 兆元）的人，遠超排名第二的任何一人。",
    "thread_text": (
        "馬斯克成全球首位兆億富翁\n\n"
        "Elon Musk——Tesla、SpaceX、X 的老闆——如今成為全球有史以來第一位個人身價超過 1 兆美元（約新台幣 32 兆元）的人。\n\n"
        "1 兆美元是什麼概念？台灣全年 GDP 大約是 7,700 億美元，"
        "他的身價已超過台灣整個國家一年的產值。"
        "目前這則消息來自 BBC，細節仍待確認。\n\n"
        "—— 本則來自 BBC，2026 年 6 月 13 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "馬斯克成全球首位兆億富翁\n\n"
        "Elon Musk 如今是全球首位個人身價超過 1 兆美元（約新台幣 32 兆元）的人。"
        "他旗下有 X（前 Twitter）、Tesla 與 SpaceX。\n\n"
        "1 兆美元是什麼概念？台灣全年 GDP 大約是 7,700 億美元，"
        "他的身價已超過整個台灣一整年的生產總值。"
        "這是個人財富累積的全新里程碑。\n\n"
        "本則來自 BBC 於 2026 年 6 月 13 日發佈的報導。"
    ),
    "voice_text": (
        "Elon Musk 成了全球首位個人身價超過 1 兆美元的人。"
        "換算台幣，大概是 32 兆——比台灣整年的 GDP 還多。\n\n"
        "他同時是 Tesla、SpaceX 和 X 的老闆。"
        "在 SpaceX 剛剛 IPO 的時間點上，這個數字也因此被重新計算了一遍。"
        "目前這則消息尚只有單一報導，但結論很清楚：他是有史以來最有錢的人。"
    ),
    "confidence": "medium",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "Elon Musk 成為全球首位個人身價超過 1 兆美元的人",
            "source_id": "bbc_technology",
            "source_title": "Who is Elon Musk and what is his net worth?",
            "source_url": "https://www.bbc.com/news/articles/c0r1975ded7o?at_medium=RSS&at_campaign=rss",
            "support_type": "direct"
        }
    ]
},

"daily_20260613_evt_228": {
    "headline": "法院拒阻白宮UFC格鬥賽",
    "context": "美國聯邦法官裁定，計劃在 Trump 生日當天於白宮舉辦的 UFC 綜合格鬥賽事，可以如期進行。稍早有人提出法律挑戰試圖阻止，但法院駁回申請。",
    "thread_text": (
        "法院拒阻白宮UFC格鬥賽\n\n"
        "美國聯邦法官今日裁定，"
        "將在 Trump 生日當天於白宮舉辦的 UFC 綜合格鬥賽事，可以如期進行——"
        "法院駁回了試圖叫停這場活動的法律申請。\n\n"
        "白宮裡打 UFC，本就夠奇特。"
        "有人試圖走法律途徑阻止，法官的答案是：不准攔，照辦。\n\n"
        "—— 本則來自 Al Jazeera 與 Reuters，2026 年 6 月 13 日發佈，讓圖書館員翻譯給你聽。"
    ),
    "threads_text": (
        "法院拒阻白宮UFC格鬥賽\n\n"
        "美國聯邦法官裁定，計劃在 Trump 生日當天舉辦的白宮 UFC 綜合格鬥賽事，可以如期進行。"
        "稍早有人提出法律挑戰試圖阻止，但法院駁回了這項申請。\n\n"
        "這場活動被安排在白宮舉行，規格本身就引發爭議。"
        "法律途徑走了一輪，結局是：可以辦。\n\n"
        "本則整理自 Al Jazeera 與 Reuters 於 2026 年 6 月 13 日發佈的報導。"
    ),
    "voice_text": (
        "白宮的 UFC 格鬥賽可以照辦了。"
        "聯邦法官今日裁定，駁回試圖阻止這場活動的法律申請。\n\n"
        "這場賽事安排在 Trump 生日當天、在白宮舉行。"
        "有人走法律途徑想叫停，法官的答案是：不准攔。"
    ),
    "confidence": "high",
    "opinion_level": "none",
    "claim_trace": [
        {
            "claim": "聯邦法官裁定白宮 UFC 格鬥賽可如期舉辦，駁回法律阻止申請",
            "source_id": "aljazeera_all",
            "source_title": "US judge refuses to block Trump's White House UFC fight",
            "source_url": "https://www.aljazeera.com/news/2026/6/12/us-judge-refuses-to-block-ufc-fight-at-white-house-event?traffic_source=rss",
            "support_type": "direct"
        },
        {
            "claim": "法院不攔截 Trump 在白宮舉辦的 UFC 綜合格鬥賽事",
            "source_id": "reuters_world_google_news",
            "source_title": "US judge won't block Trump's White House UFC mixed martial arts event - Reuters",
            "source_url": "https://news.google.com/rss/articles/CBMirgFBVV95cUxNb0ZMb2hlWHFMdHNIcVNXUzN3RFJRZDhhQUpqd3NjWnpnc1JmZXIxek1EcUs2OTlsTkxMclFabFRaTC11a2RtRWUzZjdvbW1RYjFWbEtoZVhMdW9FblpLcmxlU3VIOXVITWhic016T1ljZm1WVnZNX0JMZUpVdzJTQVRfZXJzbTctek93eEJLUU1WTV9ucFU5a2VNeVRFeUg3Mk9CN29ra2dpamp5VUE?oc=5",
            "support_type": "direct"
        }
    ]
},

}  # end REWRITES


def main():
    updated = 0
    skipped = 0
    for evt_id, rewrite in REWRITES.items():
        fpath = os.path.join(EVENTS_DIR, f"{evt_id}.json")
        if not os.path.exists(fpath):
            print(f"SKIP (not found): {fpath}")
            skipped += 1
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Only update allowed fields
        for field in ("headline", "context", "thread_text", "threads_text",
                      "voice_text", "confidence", "opinion_level", "claim_trace"):
            if field in rewrite:
                data[field] = rewrite[field]
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"OK: {evt_id}")
        updated += 1
    print(f"\n完成：{updated} 個事件已更新，{skipped} 個跳過。")


if __name__ == "__main__":
    main()
