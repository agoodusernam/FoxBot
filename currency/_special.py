from currency.currency_types import Job, ShopItem, BlackMarketItem

invalid_item: ShopItem = ShopItem(
        name='Invalid',
        description='Invalid item',
        price=0,
        stock=0,
)
invalid_item.invalid = True

invalid_bm_item: BlackMarketItem = BlackMarketItem(
        name='Invalid',
        description='Invalid item',
        price=0,
        stock=0,
)
invalid_bm_item.invalid = True

invalid_job = Job(
        name="Invalid",
        req_experience=0,
        salary=0,
        salary_variance=0,
)