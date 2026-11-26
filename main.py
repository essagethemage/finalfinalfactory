import asyncio
import pygame
import random
import heapq




async def main():
    pygame.init()
    width = 800
    height = 800
    screen = pygame.display.set_mode((800, 800))
    clock = pygame.time.Clock()
    grid_size = 20
    cell_size = 180
    max_w = grid_size * cell_size
    max_h = grid_size * cell_size


    health_font = pygame.font.SysFont(None, 30)
    level_font = pygame.font.SysFont(None, 40)


    queue = []  # Tracks player 3-move sequence
    playerAct_arr = [
        [0 for i in range(4)] for j in range(4)
    ]  # stores player direction pair frequencies


    grid = []


    COLOR_BG = (22, 22, 29)  # Dark slate blue
    COLOR_WALL = (145, 150, 163)  # Muted silver gray
    COLOR_VISITED = (44, 62, 80)  # Dark accent for carved rooms during generation
    COLOR_CURRENT = (241, 196, 15)  # Gold marker for the generation head


    COLOR_START = (39, 174, 96)  # Soft green
    COLOR_GOAL = (192, 57, 43)  # Soft red
    COLOR_PLAYER = (52, 152, 219)  # Bright blue
    camera_x = 0
    camera_y = 0
    player_vision = 180


    animation_speed = 0.15
    player_sheet = pygame.image.load("Project3_assets/player.png").convert_alpha()
    employee_sheet = pygame.image.load("Project3_assets/employee.png").convert_alpha()
    boss_sheet = pygame.image.load("Project3_assets/boss.png").convert_alpha()


    direction = "left"


    def load_frames(sheet, x, y, frame_width, frame_height, num_frames):
        frames = []
        for i in range(num_frames):
            frame = sheet.subsurface(
                pygame.Rect(x + i * frame_width, y, frame_width, frame_height)
            )
            frames.append(frame)
        return frames


    class Player:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.frames = load_frames(player_sheet, 0, 0, 50, 50, 2)
            self.current_frame = 0
            self.current_direction = "left"


            self.color = COLOR_PLAYER
            self.radius = cell_size // 3
            self.health = 100
            self.maxh = 100
            self.speed = 10
            self.game_state = "play"


        def updateFrame(self, moving):
            frames = self.frames
            if moving:
                self.current_frame += animation_speed
                if self.current_frame >= len(frames):
                    self.current_frame = 0
            frame = frames[int(self.current_frame)]
            # Flip image if facing left
            if self.current_direction == "up":
                frame = pygame.transform.rotate(frame, 180)
            elif self.current_direction == "right":
                frame = pygame.transform.rotate(frame, 90)
            elif self.current_direction == "left":
                frame = pygame.transform.rotate(frame, -90)
            self.image = pygame.transform.scale(frame, (150, 150))


        def takeDamage(self, damage):
            self.health -= damage


            if self.health <= 0:
                self.health = 0
                self.game_state = "die"


        def draw(self, camera_x, camera_y):
            player_circle = pygame.draw.circle(
                screen, self.color, (self.x - camera_x, self.y - camera_y), self.radius
            )


        def can_move(self, x, y, direction):
            cell_x = int(self.x // cell_size)
            cell_y = int(self.y // cell_size)


            cell = grid[cell_y][cell_x]


            if direction == "right":
                boundary = (cell_x + 1) * cell_size


                if x + self.radius > boundary:
                    if cell.walls[1]:
                        return False


            elif direction == "left":
                boundary = cell_x * cell_size


                if x - self.radius < boundary:
                    if cell.walls[3]:
                        return False


            elif direction == "down":
                boundary = (cell_y + 1) * cell_size


                if y + self.radius > boundary:


                    if cell.walls[2]:
                        return False


            elif direction == "up":
                boundary = cell_y * cell_size


                if y - self.radius < boundary:


                    if cell.walls[0]:
                        return False


            return True


            ##---


        def move(self, dx, dy):
            # self.x = self.x +dx
            # self.y =self.y +dy
            if dx != 0:
                if dx > 0:
                    direction = "right"
                else:
                    direction = "left"
                steps = max(1, int(abs(dx) / 2) + 1)
                step = dx / steps


                for _ in range(steps):
                    if self.can_move(self.x + step, self.y, direction):
                        self.x += step
                    else:
                        break
            if dy != 0:
                if dy > 0:
                    direction = "down"
                else:
                    direction = "up"
                steps = max(1, int(abs(dy) / 2) + 1)
                step = dy / steps


                for _ in range(steps):
                    if self.can_move(self.x, self.y + step, direction):
                        self.y += step
                    else:
                        break


    class Cell:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.walls = [True, True, True, True]


            self.visited = False


        def draw(self, surface, camera_x=0, camera_y=0):
            x = self.x * cell_size - camera_x
            y = self.y * cell_size - camera_y


            if self.x == 0 and self.y == 0:
                pygame.draw.rect(surface, COLOR_START, (x, y, cell_size, cell_size))


            elif self.x == grid_size - 1 and self.y == grid_size - 1:
                pygame.draw.rect(surface, COLOR_GOAL, (x, y, cell_size, cell_size))
            elif self.visited:
                pygame.draw.rect(surface, COLOR_VISITED, (x, y, cell_size, cell_size))


            if self.walls[0]:  # Top
                pygame.draw.line(surface, COLOR_WALL, (x, y), (x + cell_size, y), 2)


            if self.walls[1]:  # Right
                pygame.draw.line(
                    surface,
                    COLOR_WALL,
                    (x + cell_size, y),
                    (x + cell_size, y + cell_size),
                    2,
                )
            if self.walls[2]:  # Bottom
                pygame.draw.line(
                    surface,
                    COLOR_WALL,
                    (x + cell_size, y + cell_size),
                    (x, y + cell_size),
                    2,
                )
            if self.walls[3]:  # Left
                pygame.draw.line(surface, COLOR_WALL, (x, y + cell_size), (x, y), 2)


    def get_cam(player):
        camera_x = player.x - width // 2
        camera_y = player.y - height // 2


        camera_x = max(0, min(camera_x, max_w - width))
        camera_y = max(0, min(camera_y, max_h - height))
        
        return camera_x, camera_y


    def dark(surface, player, camera_x, camera_y):
        darkness = pygame.Surface((width, height), pygame.SRCALPHA)
        darkness.fill((0, 0, 0, 250))


        player_pos = (round(player.x - camera_x), round(player.y - camera_y))
        pygame.draw.circle(darkness, (0, 0, 0, 0), player_pos, player_vision)
        surface.blit(darkness, (0, 0))


    def imperf_maz(grid):


        for y in range(grid_size):


            for x in range(grid_size):
                random_num2 = random.randint(1, 10)
                random_num3 = random.randint(1, 10)
                if x < grid_size - 1:
                    if random_num2 <= 3:
                        grid[y][x].walls[1] = False
                        grid[y][x + 1].walls[3] = False
                if y < grid_size - 1:
                    if random_num3 <= 3:
                        grid[y][x].walls[2] = False
                        grid[y + 1][x].walls[0] = False


    def get_open_neighbors(current, grid):
        x = current[0]
        y = current[1]
        neighbors = []
        cell = grid[y][x]


        if cell.walls[0] == False:
            if y > 0:
                neighbors.append((x, y - 1))
        if cell.walls[1] == False:
            if x < grid_size - 1:
                neighbors.append((x + 1, y))
        if cell.walls[2] == False:
            if y < grid_size - 1:
                neighbors.append((x, y + 1))
        if cell.walls[3] == False:
            if x > 0:
                neighbors.append((x - 1, y))
        return neighbors


    def a_star(start, goal, grid):
        if start == goal:
            return [start]


        frontier = [(0, start)]
        came_from = {start: None}
        cost = {start: 0}


        while frontier:
            _, current = heapq.heappop(frontier)


            if current == goal:
                break


            for neighbor in get_open_neighbors(current, grid):
                new_cost = cost[current] + 1


                if neighbor not in cost or new_cost < cost[neighbor]:
                    cost[neighbor] = new_cost


                    priority = (
                        new_cost + abs(goal[0] - neighbor[0]) + abs(goal[1] - neighbor[1])
                    )


                    heapq.heappush(frontier, (priority, neighbor))
                    came_from[neighbor] = current
        if goal not in came_from:
            return []


        path = []
        current = goal


        while current is not None:
            path.append(current)
            current = came_from[current]


        return path[::-1]


    #grid = []  #Placed it a little earlier since it kept saying it was undefined
    stack = []
    for y in range(grid_size):
        row = []


        for x in range(grid_size):
            cell = Cell(x, y)
            row.append(cell)
        grid.append(row)


    current = grid[0][0]
    current.visited = True
    generating = True
    running = True


    class Employee:
        def __init__(self, x, y):
            self.x = x
            self.y = y


            self.radius = cell_size // 3
            self.speed = 6
            self.chase = 200
            self.change_direction = 0


            self.collide_player = False
            self.damage_timer = 0


            self.is_boss = False


            self.frames = load_frames(employee_sheet, 0, 0, 50, 50, 2)
            self.current_frame = 0
            self.current_direction = "left"


        def load_frame_update(self, is_the_boss):
            if is_the_boss:
                self.frames = load_frames(boss_sheet, 0, 0, 50, 50, 2)


        def updateFrame(self):
            frames = self.frames
            self.current_frame += animation_speed
            if self.current_frame >= len(frames):
                self.current_frame = 0
            frame = frames[int(self.current_frame)]
            # Flip image if facing left
            if self.current_direction == "up":
                frame = pygame.transform.rotate(frame, 180)
            elif self.current_direction == "right":
                frame = pygame.transform.rotate(frame, 90)
            elif self.current_direction == "left":
                frame = pygame.transform.rotate(frame, -90)
            self.image = pygame.transform.scale(frame, (150, 150))


        def draw(self, camera_x, camera_y):
            pygame.draw.circle(
                screen,
                (191, 64, 191),
                ((self.x - camera_x), (self.y - camera_y)),
                self.radius,
            )


        def detect(self, player):


            direction = pygame.Vector2(player.x - self.x, player.y - self.y)


            distance = direction.length()
            if distance < self.chase:
                return True
            else:
                return False


        def can_move(self, x, y, direction):
            cell_x = int(self.x // cell_size)
            cell_y = int(self.y // cell_size)


            cell = grid[cell_y][cell_x]


            if direction == "right":
                boundary = (cell_x + 1) * cell_size


                if x + self.radius > boundary:
                    if cell.walls[1]:
                        return False


            elif direction == "left":
                boundary = cell_x * cell_size


                if x - self.radius < boundary:
                    if cell.walls[3]:
                        return False


            elif direction == "down":
                boundary = (cell_y + 1) * cell_size


                if y + self.radius > boundary:


                    if cell.walls[2]:
                        return False


            elif direction == "up":
                boundary = cell_y * cell_size


                if y - self.radius < boundary:


                    if cell.walls[0]:
                        return False


            return True


        def move(self, player):
            if self.detect(player):
                start_x = int(self.x // cell_size)
                start_y = int(self.y // cell_size)


                goal_x = int(player.x // cell_size)
                goal_y = int(player.y // cell_size)


                path = a_star((start_x, start_y), (goal_x, goal_y), grid)


                if len(path) > 1:
                    next_cell = path[1]


                    target_x = next_cell[0] * cell_size + cell_size // 2
                    target_y = next_cell[1] * cell_size + cell_size // 2


                elif len(path) == 1:
                    target_x = player.x
                    target_y = player.y


                else:
                    return


                if target_x > self.x:
                    if self.can_move(self.x + self.speed, self.y, "right"):
                        self.x += self.speed
                        self.current_direction = "right"


                elif target_x < self.x:
                    if self.can_move(self.x - self.speed, self.y, "left"):
                        self.x -= self.speed
                        self.current_direction = "left"


                if target_y > self.y:
                    if self.can_move(self.x, self.y + self.speed, "down"):
                        self.y += self.speed
                        self.current_direction = "down"


                elif target_y < self.y:
                    if self.can_move(self.x, self.y - self.speed, "up"):
                        self.y -= self.speed
                        self.current_direction = "up"


            else:
                random_number = random.randint(0, 3)


                if random_number == 0:
                    if self.can_move(self.x, self.y - self.speed, "up"):
                        self.y -= self.speed


                elif random_number == 1:
                    if self.can_move(self.x, self.y + self.speed, "down"):
                        self.y += self.speed


                elif random_number == 2:
                    if self.can_move(self.x - self.speed, self.y, "left"):
                        self.x -= self.speed


                else:
                    if self.can_move(self.x + self.speed, self.y, "right"):
                        self.x += self.speed


    class Cheese:
        def __init__(self, x, y, type):
            self.x = x
            self.y = y
            self.type = type
            self.radius = 20


            if self.type == "mozzarella":
                self.color = (255, 253, 208)
            elif self.type == "swiss":
                self.color = (255, 255, 0)
            elif self.type == "moldy":
                self.color = (0, 128, 0)
            elif self.type == "blue":
                self.color = (0, 0, 255)


        def draw(self, screen, camera_x, camera_y):
            p1 = self.x - camera_x
            p2 = self.y - camera_y
            p3 = self.radius


            points = [(p1, p2 - p3), (p1 - p3, p2), (p1 + p3, p2 + p3)]


            pygame.draw.polygon(screen, self.color, points)


    cheesepos = []


    while len(cheesepos) < 10:
        rand_x = random.randint(0, grid_size - 1)
        rand_y = random.randint(0, grid_size - 1)


        if (rand_x, rand_y) != (0, 0):
            duplicate = False


            for pos in cheesepos:
                if pos[0] == rand_x and pos[1] == rand_y:
                    duplicate = True
            if duplicate == False:
                cheesepos.append((rand_x, rand_y))


    cheeses = []
    type_cheese = ["mozzarella", "swiss", "moldy", "blue"]
    for i in range(10):
        x = cheesepos[i][0] * cell_size + cell_size // 2
        y = cheesepos[i][1] * cell_size + cell_size // 2


        random_type = random.choice(type_cheese)
        cheeses.append(Cheese(x, y, random_type))


    blue_cheese = False
    for cheese in cheeses:
        if cheese.type == "blue":
            blue_cheese = True


    if blue_cheese == False:
        cheeses[0].type = "blue"
        cheeses[0].color = (0, 0, 255)


    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    neighbors = [2, 3, 0, 1]


    while generating:
        possible_move = []
        for i in range(4):
            dx = directions[i][0]
            dy = directions[i][1]


            x_change = current.x + dx
            y_change = current.y + dy


            if 0 <= x_change < grid_size and 0 <= y_change < grid_size:
                neighbor = grid[y_change][x_change]


                if neighbor.visited == False:
                    possible_move.append((neighbor, i))


        if len(possible_move) > 0:
            random_move = random.choice(possible_move)
            next_cell = random_move[0]
            direction = random_move[1]


            stack.append(current)
            current.walls[direction] = False
            next_cell.walls[neighbors[direction]] = False


            next_cell.visited = True
            current = next_cell
        else:
            if len(stack) > 0:
                current = stack.pop()


            else:
                generating = False


    imperf_maz(grid)


    player = Player(cell_size // 2, cell_size // 2)
    employees = []
    for i in range(10):
        rand_x = random.randint(0, grid_size - 1)
        rand_y = random.randint(0, grid_size - 1)


        x = (rand_x * cell_size) + cell_size // 2
        y = (rand_y * cell_size) + cell_size // 2


        employee = Employee(x, y)
        employees.append(employee)


    level = 1
    level_timer = pygame.time.get_ticks()
    game_over_timer = None
    boss = None
    win = False


    while running:
        screen.fill(COLOR_BG)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()


        speed = player.speed
        dx = 0
        dy = 0


        moving = False
        if keys[pygame.K_LEFT]:
            dx = -speed
            queue.append(3)  # TRACKS LEFTT MOVEMENTS
            player.current_direction = "left"
            moving = True
        if keys[pygame.K_RIGHT]:
            dx = speed
            queue.append(2)  # TRACKS RIGHT
            player.current_direction = "right"
            moving = True
        if keys[pygame.K_DOWN]:
            dy = speed
            queue.append(1)  # TRACKS DOWN
            player.current_direction = "down"
            moving = True
        if keys[pygame.K_UP]:
            dy = -speed
            queue.append(0)  # TRACKS UP
            player.current_direction = "up"
            moving = True


        player.move(dx, dy)
        if level == 2:
            end_x = player.x // cell_size
            end_y = player.y // cell_size


            if end_x == grid_size - 1 and end_y == grid_size - 1:
                win = True


        zoom_surface = pygame.Surface((max_w, max_h))
        for row in grid:
            for cell in row:
                cell.draw(zoom_surface)
                ##cell.draw()


        camera_x, camera_y = get_cam(player)
        screen.blit(zoom_surface, (-camera_x, -camera_y))
        for cheese in cheeses:
            cheese.draw(screen, camera_x, camera_y)


            distance = pygame.Vector2(player.x - cheese.x, player.y - cheese.y).length()
            if distance < player.radius + cheese.radius:
                if cheese.type == "mozzarella":
                    player.health += 10
                    if player.health > player.maxh:
                        player.health = player.maxh


                elif cheese.type == "swiss":
                    player.speed += 2


                elif cheese.type == "moldy":
                    player.takeDamage(20)
                elif cheese.type == "blue":
                    level = 2
                    player.health = 100
                    level_timer = pygame.time.get_ticks()


                    employees = []
                    boss_x = random.randint(0, grid_size - 1)
                    boss_y = random.randint(0, grid_size - 1)


                    boss_x = boss_x * cell_size + cell_size // 2
                    boss_y = boss_y * cell_size + cell_size // 2


                    boss = Employee(boss_x, boss_y)
                    boss.speed = 10
                    boss.chase = 400
                    boss.load_frame_update(True)
                    employees.append(boss)
                cheeses.remove(cheese)


                break


        # player.draw(camera_x, camera_y)


        for employee in employees:
            employee.updateFrame()
            screen.blit(
                employee.image, (employee.x - camera_x - 75, employee.y - camera_y - 80)
            )


        if level == 1:
            for employee in employees:
                employee.move(player)
                # employee.draw(camera_x, camera_y)


                distance = pygame.Vector2(
                    player.x - employee.x, player.y - employee.y
                ).length()


                if distance < player.radius + employee.radius:
                    if employee.collide_player == False:
                        player.takeDamage(10)
                        employee.collide_player = True
                else:
                    employee.collide_player = False


        elif level == 2:


            boss.move(player)
            boss.draw(camera_x, camera_y)


            distance = pygame.Vector2(player.x - boss.x, player.y - boss.y).length()
            if distance < player.radius + boss.radius:
                current_time = pygame.time.get_ticks()


                if current_time - boss.damage_timer >= 400:
                    player.takeDamage(15)
                    boss.damage_timer = current_time


            else:
                boss.damage_timer = pygame.time.get_ticks()


        dark(screen, player, camera_x, camera_y)
        text = health_font.render("Health: " + str(player.health), True, (191, 64, 191))
        screen.blit(text, (650, 20))
        if level == 2:
            current_timer = pygame.time.get_ticks()


            if current_timer - level_timer < 2000:
                level_text1 = level_font.render(
                    "Your moves are sharp (like sharp cheeder... (ʘ‿ʘ)╯",
                    True,
                    (255, 255, 255),
                )
                screen.blit(level_text1, (20, 20))


                level_text2 = level_font.render(
                    "Level 2: Find exit to escape", True, (255, 255, 255)
                )
                screen.blit(level_text2, (20, 80))


        # ______________TRANSITION MATRIX START_________________________________-


        if len(queue) == 3:


            #  print("|  UP = 0  |  DOWN = 1  |  RIGHT = 2  |  LEFT = 3  |")
            #  print("Initial Queue: ", queue)
            prob_denom = 0
            next_move = 0
            for i in range(
                len(queue) - 1
            ):  # Records registered combos in 3 player moves


                playerAct_arr[queue[i]][queue[i + 1]] += 1  # records 2-move combos
                #  print("Current Frequencies: ", playerAct_arr)


                # find highest frequency in row
                highest_val = playerAct_arr[queue[i]][queue[0]]
                for c in range(4):
                    prob_denom += playerAct_arr[queue[i]][c]


                    if highest_val < playerAct_arr[queue[i]][c]:
                        highest_val = playerAct_arr[queue[i]][c]
                        next_move = c


                prob_Act = highest_val / prob_denom
                # print("current i :", i)
                # print( "current c :", c)
            #  print("Highest Probability :", prob_Act)
            #  print("Player's next move: ", next_move)


            # print("Recorded Pairs: ", playerAct_arr)
            queue.pop(0)
        #   print("Popped Queue: ", queue)


        # ______________TRANSITION MATRIX END___________________________________


        if player.game_state == "die":
            if game_over_timer == None:
                game_over_timer = pygame.time.get_ticks()


            end_text = level_font.render("BYE BYE", True, (255, 0, 0))
            screen.blit(end_text, (20, 20))


            if pygame.time.get_ticks() - game_over_timer >= 2000:
                running = False


        if win == True:
            if game_over_timer == None:
                game_over_timer = pygame.time.get_ticks()


            end_text = level_font.render("WINN", True, (255, 0, 0))
            screen.blit(end_text, (20, 20))


            if pygame.time.get_ticks() - game_over_timer >= 2000:
                running = False


        player.updateFrame(moving)
        screen.blit(player.image, (player.x - camera_x - 75, player.y - camera_y - 80))


        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)
    pygame.quit()


asyncio.run(main())
    


