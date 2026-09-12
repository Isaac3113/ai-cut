import time
import unittest

from PIL import Image, ImageChops

from talking_head_editor.timeline import DEFAULT_STYLE
from talking_head_editor.util import ROOT, EditorError
from talking_head_editor.visuals import graphic_image


class TeachingGraphics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = ROOT / "work" / f"teaching-graphics-{time.time_ns()}"
        cls.folder.mkdir(parents=True)

    def render(self, graphic, name, size=(1920, 1080)):
        output = self.folder / (name+".png")
        result = graphic_image(graphic, output, *size, DEFAULT_STYLE)
        self.assertIsNone(result)
        with Image.open(output) as image:
            return image.convert("RGB")

    def test_steps_reveal_in_place_and_reserve_subtitle_area(self):
        for typ in ("flow", "states"):
            images = []
            for count in (1, 2, 3):
                graphic = {"type": typ, "title": "系统工作流程", "nodes": ["平台来客", "自动跟进", "数据复盘"],
                           "visible_count": count, "active_index": count-1}
                image = self.render(graphic, f"{typ}-{count}")
                safe = image.crop((0, 870, 1920, 1080))
                expected = Image.new("RGB", safe.size, DEFAULT_STYLE["background"])
                self.assertIsNone(ImageChops.difference(safe, expected).getbbox())
                colors = image.getcolors(image.width*image.height)
                self.assertGreater(sum(n for n,c in colors if c == (67, 213, 232)), 5000)
                images.append(image)
            self.assertIsNotNone(ImageChops.difference(images[0], images[1]).getbbox())
            self.assertIsNotNone(ImageChops.difference(images[1], images[2]).getbbox())
            # Unrevealed node fill disappears after all three labels have appeared.
            self.assertNotIn((23, 42, 61), dict((c,n) for n,c in images[-1].getcolors(1920*1080)))

    def test_only_sequential_flow_draws_connection_arrows(self):
        base = {"title": "系统工作流程", "nodes": ["平台来客", "自动跟进", "数据复盘"],
                "visible_count": 3, "active_index": 2}
        flow = self.render({**base, "type": "flow"}, "arrows")
        states = self.render({**base, "type": "states"}, "no-arrows")
        # These rectangles lie only in the gaps between the three node panels.
        for box in ((652, 463, 696, 498), (1224, 463, 1268, 498)):
            flow_colors = flow.crop(box).getcolors(2000)
            state_colors = states.crop(box).getcolors(2000)
            self.assertTrue(any(c == (67, 213, 232) for _,c in flow_colors))
            self.assertFalse(any(c == (67, 213, 232) for _,c in state_colors))

    def test_portrait_pip_and_banner_are_readable_sizes(self):
        self.render({"type": "flow", "title": "CRM 跟进流程", "nodes": ["平台来客", "自动回复", "团队复盘"],
                     "visible_count": 3, "active_index": 1}, "portrait", (1080, 1920))
        self.render({"type": "states", "title": "客户状态", "nodes": ["待回复", "已购买", "无兴趣"],
                     "visible_count": 2, "active_index": 1}, "pip", (806, 324))
        image = self.render({"type": "keywords", "title": "客户在哪一步，一眼看到", "subtitle": "用真实客户数据做每月复盘"},
                            "banner", (998, 172))
        self.assertEqual(image.size, (998, 172))

    def test_old_call_without_reveal_state_and_bar_remain_supported(self):
        self.render({"type": "flow", "title": "流程", "nodes": ["第一步", "第二步"]}, "all-visible", (960, 540))
        self.render({"type": "bar", "title": "校准图表", "items": [{"label": "A", "value": 10}, {"label": "B", "value": 20}]},
                    "bar", (960, 540))

    def test_invalid_stage_and_overlong_text_are_rejected(self):
        base = {"type": "flow", "title": "步骤", "nodes": ["A", "B", "C"]}
        for state in ({"visible_count": 0}, {"visible_count": 4}, {"visible_count": True},
                      {"visible_count": 1, "active_index": 1}, {"active_index": -1}, {"active_index": True}):
            with self.subTest(state=state):
                with self.assertRaises(EditorError) as caught:
                    self.render({**base, **state}, "invalid")
                self.assertEqual(caught.exception.code, "graphic_state")
        with self.assertRaises(EditorError):
            self.render({"type": "keywords", "title": "过长内容"*200, "subtitle": "更多文字"}, "overflow", (998, 172))


if __name__ == "__main__":
    unittest.main()
