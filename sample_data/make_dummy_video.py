import cv2
import numpy as np

def make_dummy_video(output_path: str, width: int = 1280, height: int = 720, fps: int = 25, seconds: int = 5):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    num_frames = fps * seconds
    # Create a few moving circles to simulate motion
    rng = np.random.default_rng(42)
    num_objs = 8
    centers = rng.integers(low=50, high=min(width, height) - 50, size=(num_objs, 2)).astype(np.float32)
    velocities = rng.uniform(low=-3, high=3, size=(num_objs, 2)).astype(np.float32)
    radii = rng.integers(low=15, high=35, size=(num_objs,))

    for _ in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (40, 40, 40)  # dark background

        for i in range(num_objs):
            centers[i] += velocities[i]
            # bounce off walls
            if centers[i][0] < radii[i] or centers[i][0] > width - radii[i]:
                velocities[i][0] *= -1
            if centers[i][1] < radii[i] or centers[i][1] > height - radii[i]:
                velocities[i][1] *= -1

            cv2.circle(frame, (int(centers[i][0]), int(centers[i][1])), int(radii[i]), (0, 255, 255), -1)

        # Overlay timestamp
        cv2.putText(frame, "Dummy CCTV", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        writer.write(frame)

    writer.release()

if __name__ == "__main__":
    out = "poultry_video.mp4"
    make_dummy_video(out)
    print(f"Wrote dummy video to {out}")
