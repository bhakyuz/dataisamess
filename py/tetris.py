import random
from abc import ABC, abstractproperty

import pandas as pd


class BlockTetrisBase(ABC):
    # type: str = abstractproperty()
    df: pd.DataFrame = abstractproperty()
    position: int = 0

    # def __post_init__(self):
    #     self.df = self.df.replace(0, pd.NA)

    def rotate(self):
        # anti-clokwise
        new = self.df.transpose().sort_index(ascending=False).reset_index(drop=True)
        self.df = new
        self.position = (self.position + 1) % 4

    def set_position(self, position: int):
        diff = ((position - self.position) + 4) % 4
        for i in range(0, diff):
            self.rotate()


class BlockI(BlockTetrisBase):
    df = pd.DataFrame({0: [1, 1, 1]}) * 1


class BlockT(BlockTetrisBase):
    df = pd.DataFrame({0: [1, 1, 1], 1: [0, 1, 0]}) * 2


class BlockL(BlockTetrisBase):
    df = pd.DataFrame({0: [1, 1, 1], 1: [0, 0, 1]}) * 3


class BlockZ(BlockTetrisBase):
    df = pd.DataFrame({0: [1, 1, 0], 1: [0, 1, 0], 2: [0, 1, 1]}) * 4


class Wall(ABC):
    def set_dims(self, length, height):
        self.length = length
        self.height = height
        self.df: pd.DataFrame = pd.DataFrame(
            pd.DataFrame(columns=range(0, self.length), index=range(0, self.height))
        )

    def place(self, x: int, y: int, block: BlockTetrisBase):
        block_copy = block.df.copy().reset_index(drop=True)
        nb_rows, nb_cols = block_copy.shape
        footprint = (
            self.df.iloc[x : x + nb_rows, y : y + nb_cols].copy().reset_index(drop=True)
        )
        # TODO needs to be fixed when there is no more place int the wall
        footprint.columns = range(0, nb_cols)
        check = footprint.fillna(0) + block_copy.fillna(0)
        comparison = (check == block_copy).where(~block_copy.isna(), True)
        is_ok = (~comparison).astype(int).sum().sum() == 0
        if is_ok:
            self.df.iloc[x : x + nb_rows, y : y + nb_cols] = block_copy
        else:
            return None


piece_l = BlockL()
piece_i = BlockI()
piece_z = BlockZ()
piece_t = BlockT()
empty_wall = Wall()
empty_wall.set_dims(10, 10)
# empty_wall.df.iloc[0, 0] = 5
print(empty_wall.df)
# empty_wall.place(0, 0, piece_l)
# print(empty_wall.df)
# empty_wall.place(1, 2, piece_i)
# print(empty_wall.df)

pieces = [piece_i, piece_l, piece_z, piece_t]
for row in range(0, 7):
    for col in range(7):
        random_piece: BlockTetrisBase = pieces[random.randint(0, 3)]
        random_position = random.randint(0, 3)
        random_piece.set_position(random_position)
        empty_wall.place(row, col, random_piece)
        # print(empty_wall.df)


print(empty_wall.df.fillna(0).to_csv(index=False))
