import skill as sk
from skill import Skill, SkillInfo, skill_info_dict, BallMatrix
from player import Player

from collections import defaultdict
import re


class Game:
    """
    游戏一回合的执行逻辑：
        玩家选择招式
        玩家选择目标
        执行先攻招式：
            写轮眼选择招式和目标
        执行空间招式
        执行状态招式
        执行主动招式：
            创建球实例存入玩家球邻接表
            处理重复心转身
            清零被魂吸玩家的查克拉
        执行篡改招式：
            处理重复万象天引
            篡改球的源和目标
        处理球抵消
        执行球效果
        判断游戏结束
        更新玩家状态
        看透玩家选择招式
    """

    def __init__(self, player_num):
        self.round_count = 1

        self.player_num = player_num
        self.players = [Player(i) for i in range(player_num)]

        self.skill_ids = [-1] * player_num
        self.skill_targets = [[] for _ in range(player_num)]
        self.preselected_skill_ids = [-1] * player_num
        self.preselected_skill_targets = [[] for _ in range(player_num)]

        self.skill_instances = []
        self.ball_matrix = BallMatrix(player_num)

    def is_game_over(self):
        return len(self.get_available_players()) <= 1

    def get_available_players(self) -> list[Player]:
        """
        获取存活（包括秽土）玩家的列表

        Returns:
            list[Player]: 存活（包括秽土）玩家的列表
        """
        return [player for player in self.players if player.is_available()]

    def get_exposed_players(self) -> list[Player]:
        """
        获取被看透的玩家列表

        Returns:
            list[Player]: 被看透的玩家列表
        """
        return [player for player in self.get_available_players() if player.is_exposed]

    def get_movable_players(self) -> list[Player]:
        """
        获取能行动的玩家

        Returns:
            list[Player]: 能行动的玩家列表
        """
        return [
            player
            for player in self.get_available_players()
            if player not in self.get_exposed_players()
        ]

    def get_leagl_skills(self, player: Player) -> list[SkillInfo]:
        """
        根据玩家蓝量获取可释放的招式信息列表，如果玩家无法行动或被看透，则返回空列表

        Args:
            player (Player): 目标玩家

        Returns:
            list[SkillInfo]: 招式信息列表
        """
        # 封穴
        if player.is_acupoint_sealed():
            print(f"{player} 被封穴")
            return [skill_info_dict[sk.MEDITATION_ID]]
        # 普通招式
        legal_skills = [
            skill_info_dict[skill_id]
            for skill_id in range(sk.SKILL_NUM)
            if skill_id not in sk.SIX_PATHS_SKILL_IDS
            and skill_info_dict[skill_id].cost <= player.mp
        ]
        # 六道招式
        if player.is_in_sixpaths_mode():
            sixpath_skills = [
                skill_info_dict[skill_id] for skill_id in sk.SIX_PATHS_SKILL_IDS
            ]
            legal_skills.extend(sixpath_skills)

        legal_skills = sorted(legal_skills, key=lambda s: s.id)

        return legal_skills

    def get_imitable_skills(self, source: Player) -> list[SkillInfo]:
        """
        获取写轮眼可复制的招式信息列表

        Args:
            source (Player): 写轮眼使用者

        Returns:
            list[SkillInfo]: 可复制招式信息列表
        """
        imitable_skill_ids = []

        for target in self.get_available_players():
            if target == source or target.is_in_kamui_zone != source.is_in_kamui_zone:
                continue

            target_skill_id = self.skill_ids[target.id]

            if target_skill_id == sk.SHARINGAN_ID:
                continue

            imitable_skill_ids.append(target_skill_id)
        
        imitable_skill_ids = sorted(imitable_skill_ids)

        return [skill_info_dict[skill_id] for skill_id in imitable_skill_ids]

    def get_legal_skill_targets(self, source: Player) -> list[Player]:
        """
        根据玩家空间状态获取可选择的目标列表

        Args:
            source (Player): 源玩家
            skill_id (int): 使用的招式

        Returns:
            list[Player]: 目标列表
        """
        legal_targets = [
            target
            for target in self.get_available_players()
            if source != target and source.is_in_kamui_zone == target.is_in_kamui_zone
        ]

        # 医疗忍术、秽土转生的目标可以是自己
        if (
            self.skill_ids[source.id] == sk.HEAL_ID
            or self.skill_ids[source.id] == sk.IMPURE_WORLD_REINCARNATION_ID
        ):
            legal_targets.append(source)

        # 秽土转生的目标可以是没被封禁的死人
        if self.skill_ids[source.id] == sk.IMPURE_WORLD_REINCARNATION_ID:
            legal_targets.extend(
                [
                    player
                    for player in self.players
                    if not player.is_available()
                    and player.is_in_kamui_zone == source.is_in_kamui_zone
                ]
            )

        # 天送之术的目标可以是除自己外的任何玩家
        if self.skill_ids[source.id] == sk.HEAVENLY_TRANSFER_ID:
            legal_targets.extend(
                [player for player in self.players if not player.is_available()]
            )

        legal_targets = sorted(legal_targets, key=lambda target: target.id)

        return legal_targets

    def load_exposed_selection(self):
        """
        将预选择的招式载入
        """
        for player in self.get_exposed_players():
            # 预选择的招式
            preselected_skill_id = self.preselected_skill_ids[player.id]

            if preselected_skill_id != -1:
                print(
                    f"{player} 看透，已选择招式：{skill_info_dict[preselected_skill_id].name}"
                )

                self.skill_ids[player.id] = preselected_skill_id

                self.preselected_skill_ids[player.id] = -1

            # 预选择的目标
            preselected_targets = self.preselected_skill_targets[player.id]

            if preselected_targets:
                print(
                    f"{player} 看透，已选择目标：{', '.join([target.__str__() for target in preselected_targets])}"
                )

                self.skill_targets[player.id] = preselected_targets

                self.preselected_skill_targets[player.id] = []

    def select_skill_id(self, player: Player, legal_skills: list[SkillInfo]) -> int:
        """
        玩家选择招式编号

        Args:
            player (Player): 使用招式的玩家
            legal_skills (list[SkillInfo]): 可选招式信息

        Returns:
            int: 招式编号
        """
        if not legal_skills or legal_skills[0] == sk.NONE_ACTION_ID:
            print(f'{player} 不需要选择招式')
            return -1

        if player.is_human:
            skill_id = self.user_select_skill_id(legal_skills)
            
            print(f'{player} 选择了 <{skill_info_dict[skill_id].name}>')
            return skill_id

    def select_skill_targets(
        self, player: Player, legal_targets: list[Player], target_num: int
    ) -> list[Player]:
        """
        玩家选择招式目标

        Args:
            player (Player): 使用招式的玩家
            legal_targets (list[Player]): 可选目标列表
            target_num (int): 目标数量

        Returns:
            list[Player]: 选择的目标列表
        """
        if target_num == 0:
            print(f'{player} 不需要选择目标')
            return []
        elif not legal_targets:
            print(f'{player} 没有可选择的目标，无效')
            return []
        elif len(legal_targets) == 1:  # 没得选
            print(f'{player} 只能选择目标 {legal_targets[0]}')
            return legal_targets * target_num

        if player.is_human:
            targets = self.user_select_skill_targets(legal_targets, target_num)
            
            print(f'{player} 选择了 {[t.__str__() for t in targets]}')
            return targets

    def handle_skill_ids_selection(self, is_preselection=False):
        """
        正常玩家选择招式或看透玩家选择招式

        Args:
            player_list (list[Player]): 玩家列表
            id_list (list[int]): 存储选择的 id 的目的地
        """
        player_list = (
            self.get_exposed_players()
            if is_preselection
            else self.get_movable_players()
        )
        id_list = self.preselected_skill_ids if is_preselection else self.skill_ids

        for player in player_list:
            if is_preselection:
                print(f"{player} 开始预选招式")
            else:
                print(f"{player} 开始选择招式")

            legal_skills = self.get_leagl_skills(player)
            skill_id = self.select_skill_id(player, legal_skills)

            id_list[player.id] = skill_id

    def handle_skill_targets_selection(self, is_preselection=False):
        """
        正常玩家选择目标或看透玩家选择目标

        Args:
            player_list (list[Player]): 玩家列表
            target_list (list[Player]): 存储选择的 target 的目的地
        """
        player_list = (
            self.get_exposed_players()
            if is_preselection
            else self.get_movable_players()
        )
        target_list = (
            self.preselected_skill_targets if is_preselection else self.skill_targets
        )

        for player in player_list:
            if is_preselection:
                print(f"{player} 开始预选 {skill_info_dict[self.preselected_skill_ids[player.id]].name}  的目标")
            else:
                print(f"{player} 开始选择 {skill_info_dict[self.skill_ids[player.id]].name} 的目标")

            skill_id = (
                self.preselected_skill_ids[player.id]
                if is_preselection
                else self.skill_ids[player.id]
            )
            legal_targets = self.get_legal_skill_targets(player)
            target_num = skill_info_dict[skill_id].target_num
            targets = self.select_skill_targets(player, legal_targets, target_num)

            target_list[player.id] = targets

    def instantiate_skill(
        self, skill_id: int, source: Player, targets: list[Player]
    ) -> Skill:
        """
        实例化招式

        Args:
            skill_id (int): 招式编号
            source (Player): 源
            targets (list[Player]): 目标

        Returns:
            Skill: 招式实例
        """
        if not targets and skill_info_dict[skill_id].target_num:
            return None

        ball_matrix = self.ball_matrix
        skill_instance = None

        if skill_id == sk.MEDITATION_ID:
            skill_instance = sk.Meditation(source)  # 打坐
        elif skill_id == sk.HEAL_ID:
            skill_instance = sk.Heal(source, targets[0])  # 医疗忍术
        elif skill_id == sk.RASENGAN_ID:
            skill_instance = sk.Rasengan(source, targets, ball_matrix)  # 螺旋丸
        elif skill_id == sk.REVOLVING_HEAVEN_ID:
            skill_instance = sk.RevolvingHeaven(source, ball_matrix)  # 回天
        elif skill_id == sk.SHADOW_BINDING_ID:
            skill_instance = sk.ShadowBinding(
                source, targets, ball_matrix
            )  # 影子束缚术
        elif skill_id == sk.BYAKUGAN_ID:
            skill_instance = sk.Byakugan(source, targets[0])  # 白眼
        elif skill_id == sk.TWIN_RASENGAN_ID:
            skill_instance = sk.TwinRasengan(source, targets, ball_matrix)  # 螺旋连丸
        elif skill_id == sk.CHIDORI_ID:
            skill_instance = sk.Chidori(source, targets, ball_matrix)  # 千鸟
        elif skill_id == sk.EIGHT_TRIGRAMS_SIXTY_FOUR_PALMS_ID:
            skill_instance = sk.EightTrigramsSixtyFourPalms(
                source, targets, ball_matrix
            )  # 八卦六十四掌
        elif skill_id == sk.MIND_BODY_SWITCH_ID:
            skill_instance = sk.MindBodySwitch(
                source, targets, ball_matrix
            )  # 心转身之术
        elif skill_id == sk.DEATH_CONTROLLING_POSSESSED_BLOOD_ID:
            skill_instance = sk.DeathControllingPossessedBlood(
                source, targets[0]
            )  # 死司凭血
        elif skill_id == sk.SHADOW_CLONE_ID:
            skill_instance = sk.ShadowClone(source)  # 影分身之术
        elif skill_id == sk.RASENSHURIKEN_ID:
            skill_instance = sk.Rasenshuriken(
                source, targets, ball_matrix
            )  # 螺旋手里剑
        elif skill_id == sk.MIRROR_RETURN_ID:
            skill_instance = sk.MirrorReturn(source, ball_matrix)  # 镜反
        elif skill_id == sk.SHARINGAN_ID:
            skill_instance = sk.Sharingan(source, targets[0])  # 写轮眼
        elif skill_id == sk.CHIDORI_CURRENT_ID:
            targets = self.get_legal_skill_targets(source)  # 千鸟流的对象是所有其他玩家
            skill_instance = sk.ChidoriCurrent(source, targets, ball_matrix)  # 千鸟流
        elif skill_id == sk.SIX_PATHS_MODE_ID:
            skill_instance = sk.SixPathsMode(source)  # 六道模式
        elif skill_id == sk.SHINRA_TENSEI_ID:
            skill_instance = sk.ShinraTensei(source, ball_matrix)  # 神罗天征
        elif skill_id == sk.BANSHOUTENIN_ID:
            skill_instance = sk.Banshoutenin(source, ball_matrix)  # 万象天引
        elif skill_id == sk.NARAKA_PATH_ID:
            skill_instance = sk.NarakaPath(source)  # 地狱道
        elif skill_id == sk.HUMAN_PATH_ID:
            skill_instance = sk.HumanPath(source, targets, ball_matrix)  # 人间道
        elif skill_id == sk.ANIMAL_PATH_ID:
            skill_instance = sk.AnimalPath(source)  # 畜生道
        elif skill_id == sk.ASURA_PATH_ID:
            skill_instance = sk.AsuraPath(source, targets, ball_matrix)  # 修罗道
        elif skill_id == sk.PRETA_PATH_ID:
            skill_instance = sk.PretaPath(source, ball_matrix)  # 饿鬼道
        elif skill_id == sk.IMPURE_WORLD_REINCARNATION_ID:
            skill_instance = sk.ImpureWorldReincarnatio(source, targets[0])  # 秽土转生
        elif skill_id == sk.DEAD_DEMON_CONSUMING_SEAL_ID:
            skill_instance = sk.DeadDemonConsumingSeal(source, targets[0])  # 尸鬼封尽
        elif skill_id == sk.KAMUI_ID:
            skill_instance = sk.Kamui(source)  # 神威
        elif skill_id == sk.HEAVENLY_TRANSFER_ID:
            skill_instance = sk.HeavenlyTransfer(source, targets[0])  # 天送之术
        
        if not skill_instance:
            print(f'[WARNING]: 无效技能 {source} {targets} {skill_id}')

        if not source.is_using_sharingan:   # 用写轮眼复制的招式不额外耗蓝
            source.use_mp(skill_instance.cost)
        else:
            source.use_mp(skill_info_dict[sk.SHARINGAN_ID].cost)
            source.is_using_sharingan = False   # 清空状态

        return skill_instance

    def load_selected_skills(self):
        """
        载入招式
        """
        for player in self.get_available_players():
            skill_id = self.skill_ids[player.id]
            skill_targets = self.skill_targets[player.id]

            # 无释放招式
            if skill_id == -1:
                continue
            if skill_info_dict[skill_id].target_num > len(skill_targets):
                print(f'{player} 无目标，无法发动 <{skill_info_dict[skill_id].name}>')
                continue

            skill_instance = self.instantiate_skill(skill_id, player, skill_targets)
            self.skill_instances.append(skill_instance)

    def handle_shadow_clone_skills(self):
        """
        载入影分身招式
        """
        shadow_clone_players = [
            player for player in self.get_available_players() if player.shadow_clone_num
        ]

        for player in shadow_clone_players:
            skill_id = self.skill_ids[player.id]

            while (
                player.shadow_clone_num and skill_info_dict[player.id].cost <= player.mp
            ):
                player.add_shadow_clone_num(-1)

                print(f'\n{player} 开始选择 <影分身 {player.shadow_clone_num}> 的目标')

                legal_targets = self.get_legal_skill_targets(player)
                target_num = skill_info_dict[skill_id].target_num
                targets = self.select_skill_targets(player, legal_targets, target_num)

                shadow_skill_instance = self.instantiate_skill(
                    skill_id, player, targets
                )
                self.skill_instances.append(shadow_skill_instance)

    def handle_sharingan_skills(self):
        """
        选择并载入写轮眼复制的招式
        """
        sharingan_players = [
            player
            for player in self.get_available_players()
            if self.skill_ids[player.id] == sk.SHARINGAN_ID
        ]

        for player in sharingan_players:
            print(f"\n{player} 发动 <写轮眼>， 开始选择复制的招式")
            
            player.is_using_sharingan = True

            imitable_skills = self.get_imitable_skills(player)
            skill_id = self.select_skill_id(player, imitable_skills)

            self.skill_ids[player.id] = skill_id    # 覆盖原 id
            legal_targets = self.get_legal_skill_targets(player)

            target_num = skill_info_dict[skill_id].target_num
            skill_targets = self.select_skill_targets(player, legal_targets, target_num)
            
            self.skill_targets[player.id] = skill_targets   # 覆盖原 target
            
            if skill_id == sk.NONE_ACTION_ID:   # 写轮眼无目标，失效
                print(f'{player} 的 <写轮眼> 由于无目标失效')

    def update_player_status(self):
        """
        更新玩家状态
        """
        for player in self.get_available_players():
            # 减少束缚回合
            if player.is_bound():
                player.add_bind_turns(-1)
            # 解除看透
            if player.is_exposed:
                player.is_exposed = False
            # 减少封穴回合
            if player.is_acupoint_sealed():
                player.add_acupoint_seal_turns(-1)
            # 减少六道回合
            if player.is_in_sixpaths_mode():
                player.add_sixpaths_mode_turns(-1)
            # 减少影分身
            if player.shadow_clone_num:
                player.add_shadow_clone_num(-1)

    def sort_skill_list(self):
        """
        按优先级排序招式列表
        """
        self.skill_instances = sorted(
            self.skill_instances, key=lambda skill: skill.priority
        )

    def preprocess_skill_list(self):
        """
        清除由重复导致的无效招式，并按优先级排序
        多个心转身对同一个目标无效
        多个万象天引无效
        """
        # 处理万象天引
        banshoutenin_count = len(
            [s for s in self.skill_instances if s.id == sk.BANSHOUTENIN_ID]
        )
        if banshoutenin_count > 1:
            print("存在多个万象天引，万象天引失效")
            self.skill_instances = [
                s for s in self.skill_instances if s.id != sk.BANSHOUTENIN_ID
            ]

        # 处理目标相同的心转身
        mind_body_switch_counts = defaultdict(list)
        for s in self.skill_instances:
            if s.id != sk.MIND_BODY_SWITCH_ID:
                continue

            target_id = s.targets[0].id
            mind_body_switch_counts[target_id].append(s)
            if len(mind_body_switch_counts[target_id]) > 1:
                s.is_target_repeated = True
                print(f"{s} 由于目标重复失效")
                # 处理列表内第一个心转身
                if mind_body_switch_counts[target_id][0].is_target_repeated == False:
                    mind_body_switch_counts[target_id][0].is_target_repeated = True
                    print(f"{mind_body_switch_counts[target_id][0]} 由于目标重复失效")

        self.skill_instances = [
            s
            for s in self.skill_instances
            if s.id != sk.MIND_BODY_SWITCH_ID
            or s.id == sk.MIND_BODY_SWITCH_ID
            and not s.is_target_repeated
        ]

        self.sort_skill_list()

    def apply_skills(self):
        """
        处理招式效果
        """
        self.sort_skill_list()
        # 先处理先攻招式
        priority_skills = [
            skill for skill in self.skill_instances if skill.priority == 0
        ]
        for skill in priority_skills:
            skill.apply()
        # 处理招式列表
        self.preprocess_skill_list()
        # 处理剩余招式
        other_skills = [skill for skill in self.skill_instances if skill.priority > 0]
        for skill in other_skills:
            skill.apply()

    def handle_balls_counteract(self):
        """
        处理球的抵消
        邻接矩阵上对称的位置的列表中的球会抵消，从队头依次取球，直到一个列表的球不为空
        """
        for source_id in range(self.ball_matrix.size):
            for target_id in range(source_id + 1, self.ball_matrix.size):
                source_balls = self.ball_matrix.get_balls(source_id, target_id)
                target_balls = self.ball_matrix.get_balls(target_id, source_id)
                # 不断从队头取球直到空
                while source_balls and target_balls:
                    source_ball = source_balls.pop(0)
                    target_ball = target_balls.pop(0)

                    print(f"{source_ball} 和 {target_ball} 抵消")

    def handle_balls(self):
        """
        处理球的效果
        """
        self.handle_balls_counteract()

        all_balls = self.ball_matrix.get_all_balls()

        for ball in all_balls:
            ball.apply()

    def handle_life_steal(self):
        """
        处理魂吸
        """
        for player in self.get_available_players():
            if player.is_soul_stealed:
                player.clear_mp()
                player.is_soul_stealed = False  # 解除魂吸

    def clear_skills(self):
        """
        清理选择和列表
        """
        self.skill_ids = [-1] * self.player_num
        self.skill_targets = [[] for _ in range(self.player_num)]
        self.skill_instances = []
        self.ball_matrix = BallMatrix(self.player_num)

    def user_select_skill_id(self, legal_skills: list[SkillInfo]) -> int:
        print("可选择的招式如下：")
        for skill in legal_skills:
            print(f"{skill.id}: {skill.name}")

        skill_id = input("请输入招式编号：")

        legal_skill_ids = [s.id for s in legal_skills]
        while not str.isdigit(skill_id) or int(skill_id) not in legal_skill_ids:
            print("可选择的招式如下：")
            for skill in legal_skills:
                print(f"{skill.id}: {skill.name}")
            skill_id = input(
                f"输入的编号 {skill_id} 不在合法编号 {legal_skill_ids} 内\n请输入合法编号："
            )

        return int(skill_id)

    def user_select_skill_targets(
        self, legal_targets: list[Player], target_num: int
    ) -> list[Player]:
        def is_valid_input(s: str, legal_target_ids: list[int], target_num: int):
            if not s or not all(re.fullmatch(r"-?\d+", num) for num in s.split()):
                return False

            target_ids = list(map(int, s.split()))
            if len(target_ids) != target_num:
                return False

            if any(target_id not in legal_target_ids for target_id in target_ids):
                return False

            return True

        legal_target_ids = [target.id for target in legal_targets]

        print("可选择的目标有：")
        for target in legal_targets:
            print(f"{target.id}：{target}")

        target_id_str = input(f"请输入 {target_num} 个目标（目标可重复）：")

        while not is_valid_input(target_id_str, legal_target_ids, target_num):
            print("输入有误，可选择的目标有：")
            for target in legal_targets:
                print(f"{target.id}：{target}")

            target_id_str = input(f"请输入 {target_num} 个目标（目标可重复）：")

        target_ids = list(map(int, target_id_str.split()))

        return [self.players[target_id] for target_id in target_ids]

    def run(self):
        print("游戏开始")

        while True:
            print("\n——————————————————————————————")
            print(f"开始第 {self.round_count} 回合")
            self.round_count += 1

            for player in self.players:
                player.print_status()

            # 加载预选招式
            self.load_exposed_selection()

            # 选择招式
            print("\n↓↓↓↓↓↓ 玩家开始选择招式 ↓↓↓↓↓↓↓\n")
            self.handle_skill_ids_selection()

            # 选择目标
            print("\n↓↓↓↓↓↓ 玩家开始选择目标 ↓↓↓↓↓↓↓\n")
            self.handle_skill_targets_selection()
            self.handle_shadow_clone_skills()
            self.handle_sharingan_skills()

            # 实例化
            print("\n↓↓↓↓↓↓ 玩家选择完毕，开始执行 ↓↓↓↓↓↓↓\n")
            self.load_selected_skills()

            # 更新玩家状态
            self.update_player_status()

            # 执行
            self.apply_skills()
            self.handle_balls()
            self.handle_life_steal()
            self.clear_skills()

            # 看透预选择
            print("\n------ 开始看透的预选阶段 ------\n")
            self.handle_skill_ids_selection(True)
            self.handle_skill_targets_selection(True)

            # 游戏结束判断
            if self.is_game_over():
                break

        if not self.get_available_players():
            print("\n游戏结束，平局")
        else:
            print(f"\n游戏结束, {self.get_available_players()[0]} 获胜")


if __name__ == "__main__":
    game = Game(3)
    game.run()
