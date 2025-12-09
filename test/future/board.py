import random
from typing import List, Tuple, Optional


class BoardGenerator:
    BOARD_SIZE = 10
    SHIPS = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

    def __init__(self):
        self.board: List[List[int]] = []
        self.ships: List[dict] = []

    def generate(self) -> List[dict]:
        """Генерирует случайное расположение кораблей"""

        # Сбрасываем доску
        self.board = [[0] * self.BOARD_SIZE for _ in range(self.BOARD_SIZE)]
        self.ships = []

        # Размещаем корабли от большего к меньшему
        for ship_size in self.SHIPS:
            placed = False
            attempts = 0
            max_attempts = 1000

            while not placed and attempts < max_attempts:
                attempts += 1

                # Случайное направление
                is_horizontal = random.choice([True, False])

                # Случайная позиция
                if is_horizontal:
                    x = random.randint(0, self.BOARD_SIZE - ship_size)
                    y = random.randint(0, self.BOARD_SIZE - 1)
                    cells = [[x + i, y] for i in range(ship_size)]
                else:
                    x = random.randint(0, self.BOARD_SIZE - 1)
                    y = random.randint(0, self.BOARD_SIZE - ship_size)
                    cells = [[x, y + i] for i in range(ship_size)]

                # Проверяем, можно ли разместить
                if self._can_place_ship(cells):
                    self._place_ship(cells)
                    self.ships.append({
                        "size": ship_size,
                        "cells": cells,
                        "hits": [],
                        "is_sunk": False
                    })
                    placed = True

            # Если не удалось разместить — начинаем заново
            if not placed:
                return self.generate()

        return self.ships

    def _can_place_ship(self, cells: List[List[int]]) -> bool:
        """Проверяет, можно ли разместить корабль в указанных клетках"""

        for cell in cells:
            x, y = cell[0], cell[1]

            # Проверяем саму клетку и все 8 соседних
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy

                    # Проверяем границы
                    if 0 <= nx < self.BOARD_SIZE and 0 <= ny < self.BOARD_SIZE:
                        if self.board[ny][nx] == 1:
                            return False

        return True

    def _place_ship(self, cells: List[List[int]]) -> None:
        """Размещает корабль на доске"""

        for cell in cells:
            x, y = cell[0], cell[1]
            self.board[y][x] = 1

    def print_board(self) -> None:
        """Выводит доску в консоль (для отладки)"""

        print("  0 1 2 3 4 5 6 7 8 9")
        for y in range(self.BOARD_SIZE):
            row = f"{y} "
            for x in range(self.BOARD_SIZE):
                row += "■ " if self.board[y][x] == 1 else "· "
            print(row)



def generate_board() -> List[dict]:
    """Создаёт новую доску с кораблями"""
    generator = BoardGenerator()
    return generator.generate()
