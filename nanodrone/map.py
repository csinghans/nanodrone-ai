"""nanodrone.map — a tiny 2D occupancy grid built from depth images (Lesson 14a).

Until now depth was only ever sampled at a single point (range to one target).
This builds the drone's first piece of *spatial memory*: project whole depth
columns into the world and tile the room into cells, marking the ones an obstacle
was seen in. The same grid is reused by later on-board lessons.

Geometry is shared with the rest of the course: `linearize_depth` and
`world_point` come from `nanodrone.detect` (Lesson 2). A column `cx` of the depth
image maps to a bearing the same way `detect_blob` maps a blob centroid, so a
mapped obstacle lands where the follower would have aimed.
"""

import math

import numpy as np

from .detect import linearize_depth, world_point

FOV_DEG = 60.0


class OccupancyGrid:
    """A square grid over [-extent, extent] in x and y. Cells accumulate hits;
    `occupied()` returns the cells seen often enough to trust."""

    def __init__(self, extent: float = 3.0, res: float = 0.3):
        self.extent = extent
        self.res = res
        self.n = int(round(2 * extent / res))
        self.grid = np.zeros((self.n, self.n), dtype=np.int32)

    def _cell(self, x: float, y: float):
        ix = int((x + self.extent) / self.res)
        iy = int((y + self.extent) / self.res)
        if 0 <= ix < self.n and 0 <= iy < self.n:
            return ix, iy
        return None

    def integrate(
        self,
        drone_pos,
        drone_yaw: float,
        dep,
        near: float,
        far: float,
        max_range: float = 3.5,
        col_step: int = 4,
    ) -> int:
        """Project one depth image into the grid. Uses a middle band of rows (a
        level camera sees the floor only far away there, so empty floor reads as
        out-of-range and is ignored) and marks the nearest surface per column.
        Returns the number of cells hit by this frame."""
        h, w = dep.shape[0], dep.shape[1]
        r0, r1 = int(0.40 * h), int(0.60 * h)
        half = math.radians(FOV_DEG / 2)
        hits = 0
        for cx in range(0, w, col_step):
            d = linearize_depth(float(np.min(dep[r0:r1, cx])), near, far)
            if d >= max_range:
                continue  # horizon / empty floor / background — not an obstacle
            bearing = math.degrees(math.atan(((2 * cx / w) - 1) * math.tan(half)))
            wx, wy, _ = world_point(drone_pos, drone_yaw, bearing, d)
            cell = self._cell(wx, wy)
            if cell is not None:
                self.grid[cell] += 1
                hits += 1
        return hits

    def occupied(self, min_hits: int = 3):
        """World (x, y) centres of cells hit at least `min_hits` times."""
        out = []
        for ix, iy in zip(*np.where(self.grid >= min_hits)):
            wx = (ix + 0.5) * self.res - self.extent
            wy = (iy + 0.5) * self.res - self.extent
            out.append((float(wx), float(wy), int(self.grid[ix, iy])))
        return out

    def near(self, x: float, y: float, radius: float = 0.5, min_hits: int = 3) -> bool:
        """Is any occupied cell within `radius` of (x, y)? (recall check)."""
        return any(
            math.hypot(cx - x, cy - y) <= radius
            for cx, cy, _ in self.occupied(min_hits)
        )

    def save_png(self, path: str, drone_path=None, truth=None) -> None:
        """Render the grid (lazy matplotlib import so `import` stays light)."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(5, 5))
        ax.imshow(
            self.grid.T,
            origin="lower",
            extent=[-self.extent, self.extent, -self.extent, self.extent],
            cmap="viridis",
        )
        if drone_path:
            xs, ys = zip(*drone_path)
            ax.plot(xs, ys, "w.-", lw=1, ms=2, alpha=0.7, label="drone path")
        if truth:
            tx, ty = zip(*truth)
            ax.scatter(tx, ty, c="red", marker="x", s=80, label="true obstacles")
        ax.set_title("Occupancy grid (from depth)")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.legend(loc="upper right", fontsize=8)
        fig.tight_layout()
        fig.savefig(path, dpi=90)
        plt.close(fig)
