import numpy as np
import tensorflow as tf
import pymysql
from config import DB_CONFIG, PLAN_TABLE
from load_data import load_data_from_db

# -=-=-=-=-=-=-=-
# Ustawienia
# -=-=-=-=-=-=-=-
NUM_DNI = 5      # dni tygodnia
NUM_SLOTOW = 8   # slotów dziennie

class TimetableEnv:
    def __init__(self, data):
        self.nauczyciele = data["nauczyciele"]
        self.oddzialy = data["oddzialy"]
        self.przedmioty = data["przedmioty"]
        self.sale = data["sale"]
        plan_info = data["plan_info"]
        self.lessons = []
        for row in plan_info:
            n_id = row["NauczycielID"]
            o_id = row["OddzialID"]
            p_id = row["PrzedmiotID"]
            hours = row["TygodnioweGodziny"]
            for _ in range(hours):
                self.lessons.append((n_id, o_id, p_id))
        self.total_lessons = len(self.lessons)
        self.current_index = 0
        self.assignments = [None] * self.total_lessons

    def reset(self):
        self.current_index = 0
        self.assignments = [None] * self.total_lessons
        return np.array([self.current_index], dtype=np.int32)

    def step(self, action):
        total_days = NUM_DNI
        total_slots = NUM_SLOTOW
        total_rooms = len(self.sale)
        day = action // (total_slots * total_rooms)
        remainder = action % (total_slots * total_rooms)
        slot = remainder // total_rooms
        room = remainder % total_rooms

        lesson = self.lessons[self.current_index]
        n_id, o_id, p_id = lesson

        # Sprawdzenie konfliktu: w tym samym dniu i slocie nie może być:
        # - przypisany ten sam nauczyciel,
        # - ta sama sala,
        # - ani lekcja dla tej samej klasy (oddziału).
        conflict = False
        for idx, assign in enumerate(self.assignments):
            if assign is None:
                continue
            assigned_day, assigned_slot, assigned_room = assign
            if assigned_day == day and assigned_slot == slot:
                other_lesson = self.lessons[idx]
                if other_lesson[0] == n_id or other_lesson[1] == o_id or assigned_room == room:
                    conflict = True
                    break

        reward = -1.0 if conflict else 0.5
        if not conflict:
            self.assignments[self.current_index] = (day, slot, room)
        self.current_index += 1
        done = self.current_index >= self.total_lessons
        if done:
            bonus = self.compute_structure_bonus()
            reward += 5.0 + bonus
        next_state = np.array([self.current_index], dtype=np.int32)
        return next_state, reward, done, {}

    def compute_structure_bonus(self):
        bonus = 0.0
        for day in range(NUM_DNI):
            day_assignments = []
            for idx, assign in enumerate(self.assignments):
                if assign is not None and assign[0] == day:
                    day_assignments.append((assign[1], self.lessons[idx][2]))
            if not day_assignments:
                continue
            day_assignments.sort(key=lambda x: x[0])
            for i in range(1, len(day_assignments)):
                if day_assignments[i][1] == day_assignments[i-1][1]:
                    bonus += 1.0
            slots = [slot for slot, _ in day_assignments]
            gap = (max(slots) - min(slots) + 1) - len(slots)
            bonus += max(0, 2 - gap)
        return bonus

    def action_space_size(self):
        total_days = NUM_DNI
        total_slots = NUM_SLOTOW
        total_rooms = len(self.sale)
        return total_days * total_slots * total_rooms

class PolicyModel(tf.keras.Model):
    def __init__(self, action_space_size):
        super().__init__()
        self.dense1 = tf.keras.layers.Dense(32, activation='relu')
        self.dense2 = tf.keras.layers.Dense(32, activation='relu')
        self.logits = tf.keras.layers.Dense(action_space_size)

    def call(self, inputs):
        x = tf.cast(inputs, tf.float32)
        x = self.dense1(x)
        x = self.dense2(x)
        return self.logits(x)

def train_policy(env, model, optimizer, num_episodes=100, gamma=0.99):
    action_space = env.action_space_size()
    for episode in range(num_episodes):
        states = []
        actions = []
        rewards = []
        state = env.reset()  # shape (1,)
        done = False
        while not done:
            states.append(state)
            state_input = np.expand_dims(state, axis=0).astype(np.float32)  # (1,1)
            logits = model(state_input)  # (1, action_space)
            action_dist = tf.nn.softmax(logits)
            action = np.random.choice(action_space, p=action_dist.numpy()[0])
            actions.append(action)
            next_state, reward, done, _ = env.step(action)
            rewards.append(reward)
            state = next_state
        total_reward = np.sum(rewards)
        returns = []
        G = 0
        for r in reversed(rewards):
            G = r + gamma * G
            returns.insert(0, G)
        returns = np.array(returns, dtype=np.float32)
        returns = (returns - np.mean(returns)) / (np.std(returns) + 1e-8)
        states_tensor = tf.convert_to_tensor(np.array(states), dtype=tf.float32)  # (episode_len, 1)
        actions_tensor = tf.convert_to_tensor(np.array(actions), dtype=tf.int32)   # (episode_len,)
        returns_tensor = tf.convert_to_tensor(returns, dtype=tf.float32)           # (episode_len,)
        with tf.GradientTape() as tape:
            logits = model(states_tensor)
            action_probs = tf.nn.softmax(logits)
            indices = tf.stack([tf.range(tf.shape(action_probs)[0]), actions_tensor], axis=1)
            selected_probs = tf.gather_nd(action_probs, indices)
            log_probs = tf.math.log(selected_probs + 1e-8)
            loss = -tf.reduce_sum(log_probs * returns_tensor)
        grads = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(grads, model.trainable_variables))
        if (episode+1) % 10 == 0:
            print(f"Episode {episode+1}: Total Reward: {total_reward:.2f}, Loss: {loss.numpy():.4f}")
    return env.assignments

def save_plan_to_db(env, table_name=PLAN_TABLE):
    connection = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG["port"],
        charset=DB_CONFIG["charset"]
    )
    try:
        with connection.cursor() as cursor:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nauczyciel_id INT,
                oddzial_id INT,
                przedmiot_id INT,
                day INT,
                slot INT,
                room INT
            );
            """
            cursor.execute(create_sql)
            for i, assign in enumerate(env.assignments):
                if assign is None:
                    continue
                day, slot, room = assign
                lesson = env.lessons[i]
                nauczyciel_id, oddzial_id, przedmiot_id = lesson
                insert_sql = f"""
                INSERT INTO {table_name} (nauczyciel_id, oddzial_id, przedmiot_id, day, slot, room)
                VALUES (%s, %s, %s, %s, %s, %s);
                """
                cursor.execute(insert_sql, (nauczyciel_id, oddzial_id, przedmiot_id, day, slot, room))
        connection.commit()
        print(f"Plan został zapisany do bazy w tabeli '{table_name}'.")
    finally:
        connection.close()

def generate_plan():
    data = load_data_from_db()
    env = TimetableEnv(data)
    action_space = env.action_space_size()
    model = PolicyModel(action_space)
    optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)
    _ = train_policy(env, model, optimizer, num_episodes=100, gamma=0.99)
    save_plan_to_db(env, table_name=PLAN_TABLE)
    return env.assignments

if __name__ == "__main__":
    assignments = generate_plan()
    print("Generated Assignments:")
    print(assignments)
