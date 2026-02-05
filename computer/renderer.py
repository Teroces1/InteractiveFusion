import pygame
import numpy as np
from math import cos, sin, pi

# Configuration
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 500 
# Light source position (Top-Right-Front)
LIGHT_DIR = np.array([0.5, -1.0, 0.5]) 
LIGHT_DIR = LIGHT_DIR / np.linalg.norm(LIGHT_DIR)

class Cube:
    def __init__(self, position=[0, 0, 0], radius=80):
        self.position = np.array(position, dtype=float)
        r = radius
        # 8 Vertices
        self.vertices = np.array([
            [-r, -r,  r], [ r, -r,  r], [ r,  r,  r], [-r,  r,  r], # Front
            [-r, -r, -r], [ r, -r, -r], [ r,  r, -r], [-r,  r, -r]  # Back
        ])
        # Faces (Counter-Clockwise winding)
        self.faces = [
            [0, 1, 2, 3], # Front
            [1, 5, 6, 2], # Right
            [5, 4, 7, 6], # Back
            [4, 0, 3, 7], # Left
            [3, 2, 6, 7], # Top
            [4, 5, 1, 0]  # Bottom
        ]

class Sphere:
    def __init__(self, position=[0, 0, 0], radius=90, segments=16):
        self.position = np.array(position, dtype=float)
        self.vertices = []
        self.faces = []
        
        for i in range(segments + 1):
            lat = pi * i / segments
            for j in range(segments + 1):
                lon = 2 * pi * j / segments
                x = radius * sin(lat) * cos(lon)
                y = radius * cos(lat)
                z = radius * sin(lat) * sin(lon)
                self.vertices.append([x, y, z])
        
        self.vertices = np.array(self.vertices)

        for i in range(segments):
            for j in range(segments):
                p1 = i * (segments + 1) + j
                p2 = p1 + (segments + 1)
                # Winding order for sphere faces
                self.faces.append([p1, p1 + 1, p2 + 1, p2])

class Camera:
    def __init__(self, distance=500):
        self.distance = distance
        self.yaw = 0    
        self.pitch = 0  
        self.sensitivity = 0.005

    def update(self):
        mouse_buttons = pygame.mouse.get_pressed()
        rel_x, rel_y = pygame.mouse.get_rel()
        
        if mouse_buttons[0]:
            # Horizontal: Drag right -> Camera moves right (yaw decreases)
            self.yaw -= rel_x * self.sensitivity
            # Vertical: Drag down -> Camera moves down (pitch decreases)
            # Fixed: Flipped sign from += to -= to correct inversion
            self.pitch -= rel_y * self.sensitivity
            
            # Clamp pitch to avoid flipping at poles
            limit = pi/2 - 0.05
            self.pitch = max(-limit, min(limit, self.pitch))

class Renderer3D:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("3D Engine - Gray Shape & Red Point")
        self.clock = pygame.time.Clock()

    def rotate_point(self, point, yaw, pitch):
        # Pitch rotation (X-axis)
        rx = np.array([
            [1, 0, 0],
            [0, cos(pitch), -sin(pitch)],
            [0, sin(pitch), cos(pitch)]
        ])
        # Yaw rotation (Y-axis)
        ry = np.array([
            [cos(yaw), 0, sin(yaw)],
            [0, 1, 0],
            [-sin(yaw), 0, cos(yaw)]
        ])
        return ry @ (rx @ point)

    def render(self, shape, camera, moving_point_func):
        running = True
        start_ticks = pygame.time.get_ticks()

        while running:
            self.screen.fill((25, 25, 30))
            self.clock.tick(FPS)
            current_time = pygame.time.get_ticks() - start_ticks

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            camera.update()

            # 1. Transform all vertices based on Camera Orbit
            transformed_vertices = []
            for v in shape.vertices:
                rotated = self.rotate_point(v, camera.yaw, camera.pitch)
                rotated[2] += camera.distance # Move object into view
                transformed_vertices.append(rotated)

            # 2. Prepare Render Queue (Faces and Point)
            render_queue = []

            # Process Faces
            for face_indices in shape.faces:
                points = [transformed_vertices[i] for i in face_indices]
                
                # Normal Calculation (Cross Product)
                v1 = points[1] - points[0]
                v2 = points[-1] - points[0]
                normal = np.cross(v1, v2)
                norm_len = np.linalg.norm(normal)
                
                if norm_len == 0: continue
                normal /= norm_len

                # Backface Culling (If normal points away from camera, don't draw)
                if normal[2] < 0:
                    # Shading: Dot product of normal and light
                    view_light = self.rotate_point(LIGHT_DIR, camera.yaw, camera.pitch)
                    dot = np.dot(normal, -view_light)
                    intensity = max(0.15, dot) # 0.15 is ambient light
                    
                    color = (int(140 * intensity), int(140 * intensity), int(145 * intensity))
                    avg_z = sum(p[2] for p in points) / len(points)
                    
                    # Perspective Projection
                    proj_points = []
                    for p in points:
                        factor = FOV / max(1, p[2])
                        x = int(p[0] * factor + WIDTH // 2)
                        y = int(-p[1] * factor + HEIGHT // 2)
                        proj_points.append((x, y))
                    
                    render_queue.append({'z': avg_z, 'type': 'poly', 'pts': proj_points, 'color': color})

            # 3. Process Moving Point
            p_pos = moving_point_func(current_time)
            p_rot = self.rotate_point(p_pos, camera.yaw, camera.pitch)
            p_rot[2] += camera.distance
            
            if p_rot[2] > 1:
                f = FOV / p_rot[2]
                px = int(p_rot[0] * f + WIDTH // 2)
                py = int(-p_rot[1] * f + HEIGHT // 2)
                render_queue.append({'z': p_rot[2], 'type': 'point', 'pos': (px, py)})

            # 4. Painter's Algorithm: Sort by Z-depth (furthest first)
            render_queue.sort(key=lambda x: x['z'], reverse=True)

            # 5. Final Draw Pass
            for item in render_queue:
                if item['type'] == 'point':
                    pygame.draw.circle(self.screen, (255, 0, 0), item['pos'], 6)
                else:
                    pygame.draw.polygon(self.screen, item['color'], item['pts'])
                    # Subtle wireframe for definition
                    pygame.draw.polygon(self.screen, (50, 50, 55), item['pts'], 1)

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    # You can swap these to test both shapes
    shape = Cube(position=[0, 0, 0], radius=80)
    # shape = Sphere(position=[0, 0, 0], radius=90, segments=18)

    cam = Camera(distance=500)
    renderer = Renderer3D()

    def moving_point(t):
        # Parametric path for the red point
        time_s = t * 0.002
        return np.array([
            170 * cos(time_s), 
            130 * sin(time_s * 1.2), 
            170 * sin(time_s)
        ])

    renderer.render(shape, cam, moving_point)