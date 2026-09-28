from app.database import Database
from app.models.food import Food


DEFAULT_FOODS = [
    Food(food_id="F001", food_name="米饭", category="主食", initial_weight=300.0),
    Food(food_id="F002", food_name="红烧肉", category="荤菜", initial_weight=250.0),
    Food(food_id="F003", food_name="青菜", category="蔬菜", initial_weight=280.0),
    Food(food_id="F004", food_name="鸡蛋", category="蛋类", initial_weight=150.0),
]


def seed_foods(database: Database) -> None:
    """Insert the default food catalog if it does not already exist."""
    database.initialize()

    with database._connect() as conn:
        for food in DEFAULT_FOODS:
            conn.execute(
                """
                INSERT OR IGNORE INTO food
                (food_id, food_name, category, enabled, initial_weight)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    food.food_id,
                    food.food_name,
                    food.category,
                    1 if food.enabled else 0,
                    food.initial_weight,
                ),
            )

    if not database.get_suggestion_rules():
        for rule in [
            {"metric": "remaining_rate", "min_value": 0.0, "max_value": 0.10, "suggestion": "剩余率较低，可关注菜品受欢迎程度并适当调整备餐量。"},
            {"metric": "remaining_rate", "min_value": 0.10, "max_value": 0.30, "suggestion": "剩余量处于中等水平，可结合多日数据优化备餐。"},
            {"metric": "remaining_rate", "min_value": 0.30, "max_value": 1.01, "suggestion": "剩余率较高，可重点检查菜品偏好并优化供餐量。"},
        ]:
            database.save_suggestion_rule(rule)
