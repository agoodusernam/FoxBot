from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from currency.currency_types import BlackMarketCategory, BlackMarketItem, Job, JobTree, ShopCategory, ShopItem

    T = TypeVar('T', bound=Job | JobTree | ShopItem | ShopCategory)
else:
    # Python 3.14 has lazily evaluates type annotations
    T = TypeVar('T')

all_jobs: list[Job] = []
all_job_trees: list[JobTree] = []

all_shop_items: list[ShopItem] = []
all_normal_shop_items: list[ShopItem] = []
all_bm_shop_items: list[BlackMarketItem] = []

all_shop_categories: list[ShopCategory] = []
all_normal_shop_categories: list[ShopCategory] = []
all_bm_shop_categories: list[BlackMarketCategory] = []

def register_job_tree(job_tree: JobTree) -> None:
    all_job_trees.append(job_tree)
    for job in job_tree.all_jobs_flat():
        all_jobs.append(job)
    return


def _register_shop_item(item: ShopItem) -> None:
    all_shop_items.append(item)
    if isinstance(item, BlackMarketItem):
        all_bm_shop_items.append(item)
    else:
        all_normal_shop_items.append(item)


def register_shop_category(category: ShopCategory) -> None:
    all_shop_categories.append(category)
    if isinstance(category, BlackMarketCategory):
        all_bm_shop_categories.append(category)
    else:
        all_normal_shop_categories.append(category)
    
    for item in category.items:
        _register_shop_item(item)
    return


def _get_from_name(name: str, container: list[T], default: T | None = None) -> T | None:
    for item in container:
        if item.name.lower() == name.lower():
            return item
    return default


# noinspection DuplicatedCode
def job_from_str(name: str, default: Job | None = None) -> Job | None:
    return _get_from_name(name, all_jobs, default)


def job_tree_from_str(name: str) -> JobTree | None:
    return _get_from_name(name, all_job_trees)


def item_from_str(name: str) -> ShopItem | None:
    return _get_from_name(name, all_shop_items)


def normal_item_from_str(name: str) -> ShopItem | None:
    return _get_from_name(name, all_normal_shop_items)


# noinspection DuplicatedCode
def bm_item_from_str(name: str) -> BlackMarketItem | None:
    return _get_from_name(name, all_bm_shop_items)


def shop_category_from_str(name: str) -> ShopCategory | None:
    return _get_from_name(name, all_shop_categories)


def normal_category_from_str(name: str) -> ShopCategory | None:
    return _get_from_name(name, all_normal_shop_categories)


def bm_category_from_str(name: str) -> BlackMarketCategory | None:
    return _get_from_name(name, all_bm_shop_categories)