from player import Player

NONE_ACTION_ID = -1
MEDITATION_ID = 0
HEAL_ID = 1
RASENGAN_ID = 2
REVOLVING_HEAVEN_ID = 3
SHADOW_BINDING_ID = 4
BYAKUGAN_ID = 5
TWIN_RASENGAN_ID = 6
CHIDORI_ID = 7
EIGHT_TRIGRAMS_SIXTY_FOUR_PALMS_ID = 8
MIND_BODY_SWITCH_ID = 9
DEATH_CONTROLLING_POSSESSED_BLOOD_ID = 10
SHADOW_CLONE_ID = 11
RASENSHURIKEN_ID = 12
MIRROR_RETURN_ID = 13
SHARINGAN_ID = 14
CHIDORI_CURRENT_ID = 15
SIX_PATHS_MODE_ID = 16
SHINRA_TENSEI_ID = 17
BANSHOUTENIN_ID = 18
NARAKA_PATH_ID = 19
HUMAN_PATH_ID = 20
ANIMAL_PATH_ID = 21
ASURA_PATH_ID = 22
PRETA_PATH_ID = 23
IMPURE_WORLD_REINCARNATION_ID = 24
DEAD_DEMON_CONSUMING_SEAL_ID = 25
KAMUI_ID = 26
HEAVENLY_TRANSFER_ID = 27

SKILL_NUM = 28
SIX_PATHS_SKILL_IDS = [SHINRA_TENSEI_ID, BANSHOUTENIN_ID, NARAKA_PATH_ID, HUMAN_PATH_ID, ANIMAL_PATH_ID, ASURA_PATH_ID, PRETA_PATH_ID]


class Ball:
    """
    主动技能的球
    """

    def __init__(self, name: str, cost: int, source: Player, target: Player):
        self.name = name
        self.cost = cost
        self.source = source
        self.target = target

    def __str__(self):
        if self.target:
            return f"{self.source} 对 {self.target} 使用的 <{self.name}>"
        return f"{self.source} 使用的 <{self.name}>"

    def is_zone_status_available(self) -> bool:
        """
        检查球的源和目标是否在同一空间

        Returns:
            bool: 是否在同一空间
        """
        return self.source.is_in_kamui_zone == self.target.is_in_kamui_zone

    def apply(self):
        """
        球执行的对外接口
        """
        if not self.source or not self.target:
            print(f"{self} 失效")
            return

        if not self.is_zone_status_available():
            print(f"{self} 由于不在一个空间，无效")
            return

        print(f"{self} 命中")
        self.execute()

    def execute(self):
        """
        球生效逻辑
        """
        raise NotImplementedError()


class Damage(Ball):
    def __init__(
        self,
        name: str,
        cost: int,
        source: Player,
        target: Player,
        damage: int,
        life_steal: bool = False,
    ):
        super().__init__(name, cost, source, target)
        self.damage = damage
        self.life_steal = life_steal

    def execute(self):
        actual_damage = self.target.receive_damage(self.damage)

        # 吸血逻辑
        if self.life_steal:
            print(f"{self.source} 触发效果<吸血>")
            self.source.restore_hp(actual_damage)


class Bind(Ball):
    def __init__(self, name: str, cost: int, source: Player, target: Player):
        super().__init__(name, cost, source, target)

    def execute(self):
        self.target.add_bind_turns(1)


class Expose(Ball):
    def __init__(self, name: str, cost: int, source: Player, target: Player):
        super().__init__(name, cost, source, target)

    def execute(self):
        if self.target.is_exposed:
            print(f'{self.target} 已被看透，{self} 无效')
        self.target.expose()
        self.target.charmed_by = self.source


class SealAcupoint(Ball):
    def __init__(self, name: str, cost: int, source: Player, target: Player):
        super().__init__(name, cost, source, target)

    def execute(self):
        self.target.add_acupoint_seal_turns(1)


class StealSoul(Ball):
    def __init__(self, name: str, cost: int, source: Player, target: Player):
        super().__init__(name, cost, source, target)

    def execute(self):
        print(f'{self} 触发效果<魂吸>')
        self.target.is_soul_stealed = True

        target_mp = self.target.mp
        self.source.restore_mp(target_mp)


class BallMatrix:
    """
    球邻接矩阵
    """

    def __init__(self, player_num: int):
        self.size = player_num
        self.matrix = [
            [[] for _ in range(player_num)] for _ in range(player_num)
        ]  # 二维列表

    def get_balls(self, source_id: int, target_id: int) -> list[Ball]:
        return self.matrix[source_id][target_id]

    def get_all_balls(self) -> list[Ball]:
        all_balls = []

        for source in range(self.size):
            for target in range(self.size):
                all_balls.extend(self.matrix[source][target])

        return all_balls

    def insert_ball(self, source_id: int, target_id: int, ball: Ball):
        self.matrix[source_id][target_id].append(ball)


class SkillInfo:
    def __init__(self, name: str, id: int, cost: int, target_num: int):
        self.name = name
        self.id = id
        self.cost = cost
        self.target_num = target_num

skill_info_dict = {
    NONE_ACTION_ID: SkillInfo('无法行动', NONE_ACTION_ID, 0, 0),
    MEDITATION_ID: SkillInfo('打坐', MEDITATION_ID, 0, 0),
    HEAL_ID: SkillInfo('医疗忍术', HEAL_ID, 1, 1),
    RASENGAN_ID: SkillInfo('螺旋丸', RASENGAN_ID, 1, 1),
    REVOLVING_HEAVEN_ID: SkillInfo('回天', REVOLVING_HEAVEN_ID, 1, 0),
    SHADOW_BINDING_ID: SkillInfo('影子束缚术', SHADOW_BINDING_ID, 1, 1),
    BYAKUGAN_ID: SkillInfo('白眼', BYAKUGAN_ID, 1, 1),
    TWIN_RASENGAN_ID: SkillInfo('螺旋连丸', TWIN_RASENGAN_ID, 2, 2),
    CHIDORI_ID: SkillInfo('千鸟', CHIDORI_ID, 2, 1),
    EIGHT_TRIGRAMS_SIXTY_FOUR_PALMS_ID: SkillInfo('八卦六十四掌', EIGHT_TRIGRAMS_SIXTY_FOUR_PALMS_ID, 2, 1),
    MIND_BODY_SWITCH_ID: SkillInfo('心转身之术', MIND_BODY_SWITCH_ID, 2, 1),
    DEATH_CONTROLLING_POSSESSED_BLOOD_ID: SkillInfo('死司凭血', DEATH_CONTROLLING_POSSESSED_BLOOD_ID, 2, 1),
    SHADOW_CLONE_ID: SkillInfo('影分身之术', SHADOW_CLONE_ID, 2, 0),
    RASENSHURIKEN_ID: SkillInfo('螺旋手里剑', RASENSHURIKEN_ID, 3, 1),
    MIRROR_RETURN_ID: SkillInfo('镜反', MIRROR_RETURN_ID, 3, 0),
    SHARINGAN_ID: SkillInfo('写轮眼', SHARINGAN_ID, 3, 0),
    CHIDORI_CURRENT_ID: SkillInfo('千鸟流', CHIDORI_CURRENT_ID, 4, 0),
    SIX_PATHS_MODE_ID: SkillInfo('六道模式', SIX_PATHS_MODE_ID, 5, 0),
    SHINRA_TENSEI_ID: SkillInfo('神罗天征', SHINRA_TENSEI_ID, 0, 0),
    BANSHOUTENIN_ID: SkillInfo('万象天引', BANSHOUTENIN_ID, 0, 0),
    NARAKA_PATH_ID: SkillInfo('地狱道', NARAKA_PATH_ID, 0, 0),
    HUMAN_PATH_ID: SkillInfo('人间道', HUMAN_PATH_ID, 0, 1),
    ANIMAL_PATH_ID: SkillInfo('畜生道', ANIMAL_PATH_ID, 0, 0),
    ASURA_PATH_ID: SkillInfo('修罗道', ASURA_PATH_ID, 0, 4),
    PRETA_PATH_ID: SkillInfo('饿鬼道', PRETA_PATH_ID, 0, 0),
    IMPURE_WORLD_REINCARNATION_ID: SkillInfo('秽土转生', IMPURE_WORLD_REINCARNATION_ID, 6, 1),
    DEAD_DEMON_CONSUMING_SEAL_ID: SkillInfo('尸鬼封尽', DEAD_DEMON_CONSUMING_SEAL_ID, 7, 1),
    KAMUI_ID: SkillInfo('神威', KAMUI_ID, 7, 0),
    HEAVENLY_TRANSFER_ID: SkillInfo('天送之术', HEAVENLY_TRANSFER_ID, 8, 1),
}


class Skill:
    """
    招式
    """

    def __init__(self, name: str, id: int, cost: int, priority: int, source: Player):
        self.name = name
        self.id = id
        self.cost = cost
        self.priority = priority
        self.source = source

    def __str__(self):
        return f"{self.source} 使用的 <{self.name}>"

    def apply(self):
        if not self.source.is_available():
            print(f'{self.source} 已死亡，无法再使用 {self.name}')
            return
        
        print(f"{self} 发动")
        self.execute()

    def execute(self):
        raise NotImplementedError()


class PrioritySkill(Skill):
    """
    先攻招式
    """

    def __init__(self, name: str, id: int, cost: int, source: Player, target: Player):
        super().__init__(name, id, cost, 0, source)
        self.target = target

    def __str__(self):
        return f"{self.source} 对 {self.target} 使用的 <{self.name}>"
    
    def apply(self):
        # 先攻招式必定发动
        print(f"{self} 发动")
        self.execute()


class ZoneSkill(Skill):
    """
    空间招式
    """

    def __init__(self, name: str, id: int, cost: int, source: Player):
        super().__init__(name, id, cost, 1, source)


class StatusSkill(Skill):
    """
    状态招式
    """

    def __init__(self, name: str, id: int, cost: int, source: Player):
        super().__init__(name, id, cost, 2, source)


class BallSkill(Skill):
    """
    主动招式
    """

    def __init__(
        self,
        name: str,
        id: int,
        cost: int,
        source: Player,
        targets: list[Player],
        ball_matrix: BallMatrix,
    ):
        super().__init__(name, id, cost, 3, source)
        self.targets = targets
        self.ball_matrix = ball_matrix

    def __str__(self):
        return f"{self.source} 对 {', '.join([target.__str__() for target in self.targets])} 使用的 <{self.name}>"


class RewriteSkill(Skill):
    """
    篡改招式
    """

    def __init__(
        self, name: str, id: int, cost: int, source: Player, ball_matrix: BallMatrix
    ):
        super().__init__(name, id, cost, 4, source)
        self.ball_matrix = ball_matrix


class Meditation(StatusSkill):
    """
    打坐
    """

    def __init__(self, source: Player):
        super().__init__("打坐", 0, 0, source)

    def execute(self):
        self.source.restore_mp(1)


class Heal(StatusSkill):
    """
    医疗忍术
    """

    def __init__(self, source: Player, target: Player):
        super().__init__("医疗术", 1, 1, source)
        self.target = target
    
    def __str__(self):
        return f'{self.source} 对 {self.target} 使用的 <{self.name}>'
    
    def apply(self):
        if not self.source.is_available():
            print(f'{self.source} 已死亡，无法再使用 {self.name}')
            return

        if self.source.is_in_kamui_zone != self.target.is_in_kamui_zone:
            print(f'由于不在一个空间，{self} 无效')
            return
        
        print(f"{self} 发动")
        self.execute()

    def execute(self):
        self.target.restore_hp(1)


class Rasengan(BallSkill):
    """
    螺旋丸
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("螺旋丸", 2, 1, source, targets, ball_matrix)

    def execute(self):
        ball = Damage(self.name, 1, self.source, self.targets[0], 1)
        self.ball_matrix.insert_ball(
            self.source.id, self.targets[0].id, ball
        )  # 在邻接矩阵中插入球


class RevolvingHeaven(RewriteSkill):
    """
    回天
    """

    def __init__(self, source: Player, ball_matrix: BallMatrix):
        super().__init__("回天", 3, 1, source, ball_matrix)

    def execute(self):
        for player_id in range(self.ball_matrix.size):
            if player_id == self.source.id:  # 跳过自己
                continue
            # 使所有对回天使用者的球目标为空
            for ball in self.ball_matrix.get_balls(player_id, self.source.id):
                print(f'{self} 将 {ball} 抵挡')
                ball.target = None


class ShadowBinding(BallSkill):
    """
    影子束缚术
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("影子束缚术", 4, 1, source, targets, ball_matrix)

    def execute(self):
        ball = Bind(self.name, 1, self.source, self.targets[0])
        self.ball_matrix.insert_ball(
            self.source.id, self.targets[0].id, ball
        )  # 在邻接矩阵中插入球


class Byakugan(StatusSkill):
    """
    白眼
    """

    def __init__(self, source: Player, target: Player):
        super().__init__('白眼', 5, 1, source)
        self.target = target
    
    def apply(self):
        if not self.source.is_available():
            print(f'{self.source} 已死亡，无法再使用 {self.name}')
            return

        if self.source.is_in_kamui_zone != self.target.is_in_kamui_zone:
            print(f'由于不在一个空间，{self} 无效')
            return
        
        if self.target.is_exposed:
            print(f'{self.target} 已被看透，{self} 无效')
        
        print(f"{self} 发动")
        self.execute()

    def execute(self):
        self.target.expose()


class TwinRasengan(BallSkill):
    """
    螺旋连丸
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("螺旋连丸", 6, 2, source, targets, ball_matrix)

    def execute(self):
        # 遍历目标并在邻接矩阵插入球
        for target in self.targets:
            ball = Damage(self.name, 1, self.source, target, 1)
            self.ball_matrix.insert_ball(self.source.id, target.id, ball)


class Chidori(BallSkill):
    """
    千鸟
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("千鸟", 7, 2, source, targets, ball_matrix)

    def execute(self):
        ball = Damage(self.name, 2, self.source, self.targets[0], 1, True)
        self.ball_matrix.insert_ball(
            self.source.id, self.targets[0].id, ball
        )  # 在邻接矩阵中插入球


class EightTrigramsSixtyFourPalms(BallSkill):
    """
    八卦六十四掌
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("八卦六十四掌", 8, 2, source, targets, ball_matrix)

    def execute(self):
        # 伤害球
        damage_ball = Damage(self.name, 1, self.source, self.targets[0], 1)
        self.ball_matrix.insert_ball(self.source.id, self.targets[0].id, damage_ball)
        # 封穴球
        seal_acupoint_ball = SealAcupoint(self.name, 1, self.source, self.targets[0])
        self.ball_matrix.insert_ball(
            self.source.id, self.targets[0].id, seal_acupoint_ball
        )


class MindBodySwitch(BallSkill):
    """
    心转身之术
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("心转身之术", 9, 2, source, targets, ball_matrix)
        self.is_target_repeated = False

    def execute(self):
        ball = Expose(self.name, 2, self.source, self.targets[0])
        self.ball_matrix.insert_ball(
            self.source.id, self.targets[0].id, ball
        )  # 在邻接矩阵中插入球


class DeathControllingPossessedBlood(PrioritySkill):
    """
    死司凭血
    """

    def __init__(self, source: Player, target: Player):
        super().__init__("死司凭血", 10, 2, source, target)

    def execute(self):
        self.source.receive_damage(1)
        self.target.receive_damage(1)


class ShadowClone(StatusSkill):
    """
    影分身之术
    """

    def __init__(self, source: Player):
        super().__init__("影分身之术", 11, 2, source)

    def execute(self):
        self.source.add_shadow_clone_num(1)


class Rasenshuriken(BallSkill):
    """
    螺旋手里剑
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("螺旋手里剑", 12, 3, source, targets, ball_matrix)

    def execute(self):
        self.source.receive_damage(1)  # 使用者扣 1 点血

        ball = Damage(self.name, 3, self.source, self.targets[0], 3)
        self.ball_matrix.insert_ball(
            self.source.id, self.targets[0].id, ball
        )  # 在邻接矩阵中插入球


class MirrorReturn(RewriteSkill):
    """
    镜反
    """

    def __init__(self, source: Player, ball_matrix: BallMatrix):
        super().__init__("镜反", 13, 3, source, ball_matrix)

    def execute(self):
        for player_id in range(self.ball_matrix.size):
            if player_id == self.source.id:  # 跳过自己
                continue
            # 使所有对镜反使用者的球目标为源，源为目标
            for ball in self.ball_matrix.get_balls(player_id, self.source.id):
                print(f'{self} 将 {ball} 反弹')
                source = ball.source
                ball.source = ball.target
                ball.target = source


class Sharingan(PrioritySkill):
    """
    写轮眼
    """

    def __init__(self, source: Player, target: Player):
        super().__init__("写轮眼", 14, 3, source, target)
    
    def apply(self):
        print(f'{self.target} 的招式被 {self.source} 复制')


class ChidoriCurrent(BallSkill):
    """
    千鸟流
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("千鸟流", 15, 4, source, targets, ball_matrix)

    def execute(self):
        # 遍历目标并在邻接矩阵插入球
        for target in self.targets:
            ball = Damage(self.name, 1, self.source, target, 1, True)
            self.ball_matrix.insert_ball(self.source.id, target.id, ball)


class SixPathsMode(StatusSkill):
    """
    六道模式
    """

    def __init__(self, source: Player):
        super().__init__("六道模式", 16, 5, source)

    def execute(self):
        self.source.add_sixpaths_mode_turns(2)


class ShinraTensei(RewriteSkill):
    """
    神罗天征
    """

    def __init__(self, source: Player, ball_matrix: BallMatrix):
        super().__init__("神罗天征", 17, 0, source, ball_matrix)

    def execute(self):
        for player_id in range(self.ball_matrix.size):
            if player_id == self.source.id:  # 跳过自己
                continue
            # 使所有球的目标改为源
            for ball in self.ball_matrix.get_all_balls():
                print(f'{self} 将 {ball} 的目标改为 {ball.source}')
                ball.target = ball.source


class Banshoutenin(RewriteSkill):
    """
    万象天引
    """

    def __init__(self, source: Player, ball_matrix: BallMatrix):
        super().__init__("万象天引", 18, 0, source, ball_matrix)

    def execute(self):
        for player_id in range(self.ball_matrix.size):
            if player_id == self.source.id:  # 跳过自己
                continue
            # 使所有球的目标改为使用者
            for ball in self.ball_matrix.get_all_balls():
                print(f'{self} 将 {ball} 的目标改为 {self.source}')
                ball.target = self.source


class NarakaPath(StatusSkill):
    """
    地狱道
    """

    def __init__(self, source: Player):
        super().__init__("地狱道", 19, 0, source)

    def execute(self):
        self.source.restore_hp(
            self.source.max_hp
        )  # 回复生命值至最大，restore_hp 会处理上限


class HumanPath(BallSkill):
    """
    人间道
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("人间道", 20, 0, source, targets, ball_matrix)

    def execute(self):
        ball = StealSoul(self.name, 5, self.source, self.targets[0])
        self.ball_matrix.insert_ball(
            self.source.id, self.targets[0].id, ball
        )  # 在邻接矩阵中插入球


class AnimalPath(StatusSkill):
    """
    地狱道
    """

    def __init__(self, source: Player):
        super().__init__("畜生道", 21, 0, source)

    def execute(self):
        self.source.add_max_hp()


class AsuraPath(BallSkill):
    """
    修罗道
    """

    def __init__(self, source: Player, targets: list[Player], ball_matrix: BallMatrix):
        super().__init__("修罗道", 22, 0, source, targets, ball_matrix)

    def execute(self):
        # 遍历目标并在邻接矩阵插入球
        for target in self.targets:
            ball = Damage(self.name, 1, self.source, target, 1)
            self.ball_matrix.insert_ball(self.source.id, target.id, ball)


class PretaPath(RewriteSkill):
    """
    饿鬼道
    """

    def __init__(self, source: Player, ball_matrix: BallMatrix):
        super().__init__("饿鬼道", 23, 0, source, ball_matrix)

    def execute(self):
        for player_id in range(self.ball_matrix.size):
            if player_id == self.source.id:  # 跳过自己
                continue
            # 使所有对饿鬼道使用者的球目标为空，并获取查克拉
            for ball in self.ball_matrix.get_balls(player_id, self.source.id):
                ball.target = None

                print(f'{self} 触发效果 <饿鬼>')
                self.source.restore_mp(ball.cost)


class ImpureWorldReincarnatio(StatusSkill):
    """
    秽土转生
    """

    def __init__(self, source: Player, target: Player):
        super().__init__("秽土转生", 24, 6, source)
        self.target = target
    
    def apply(self):
        if not self.source.is_available():
            print(f'{self.source} 已死亡，无法再使用 {self.name}')
            return

        if self.source.is_in_kamui_zone != self.target.is_in_kamui_zone:
            print(f'由于不在一个空间，{self} 无效')
            return
        
        print(f"{self} 发动")
        self.execute()

    def execute(self):
        self.target.reanimation()


class DeadDemonConsumingSeal(PrioritySkill):
    """
    尸鬼封尽
    """

    def __init__(self, source: Player, target: Player):
        super().__init__("尸鬼封尽", 25, 7, source, target)

    def execute(self):
        self.source.fatal_seal()
        self.target.fatal_seal()


class Kamui(ZoneSkill):
    """
    神威
    """

    def __init__(self, source: Player):
        super().__init__("神威", 26, 7, source)

    def execute(self):
        self.source.switch_zone()
        
        if self.source.is_in_kamui_zone:
            print(f'{self.source} 进入神威空间')
        else:
            print(f'{self.source} 进入现实空间')


class HeavenlyTransfer(ZoneSkill):
    """
    天送之术
    """

    def __init__(self, source: Player, target: Player):
        super().__init__("天送之术", 27, 8, source)
        self.target = target
    
    def __str__(self):
        return f'{self.source} 对 {self.target} 使用的 <{self.name}>'

    def execute(self):
        self.target.switch_zone()
        
        if self.target.is_in_kamui_zone:
            print(f'{self.target} 进入神威空间')
        else:
            print(f'{self.target} 进入现实空间')