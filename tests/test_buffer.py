import unittest

from catcam.recording.buffer import PreEventBuffer


class PreEventBufferTests(unittest.TestCase):
    def test_keeps_only_last_n_frames(self) -> None:
        buffer = PreEventBuffer[int](fps=5, seconds=2)
        for index in range(12):
            buffer.append(index)

        self.assertEqual(buffer.max_frames, 10)
        self.assertEqual(buffer.snapshot(), [2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        self.assertTrue(buffer.is_full)


if __name__ == "__main__":
    unittest.main()
