from pathlib import Path

from app.config import seed_foods
from app.database import Database


def main():
    Path("data/test_food_seed.db").unlink(missing_ok=True)
    db = Database("data/test_food_seed.db")
    seed_foods(db)

    foods = db.get_foods()

    assert len(foods) == 4

    expected = {
        "F001": "米饭",
        "F002": "红烧肉",
        "F003": "青菜",
        "F004": "鸡蛋",
    }

    for food in foods:
        assert food.food_id in expected
        assert food.food_name == expected[food.food_id]
        assert food.enabled is True

    print("Food seed test passed")

    for food in foods:
        print(
            f"{food.food_id}: "
            f"{food.food_name} - "
            f"{food.category}"
        )


if __name__ == "__main__":
    main()
