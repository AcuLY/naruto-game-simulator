class Player:
    def __init__(self, id):
        self.id = id
        # 基础状态参数
        self.hp = 2
        self.mp = 100
        self.max_hp = 4
        self.is_dead = False  # 是否死亡过
        self.is_in_second_life = False  # 秽土
        self.second_hp = 2
        self.second_max_hp = 4
        # 特殊状态参数
        self.bind_turns = 0  # 束缚
        self.is_exposed = False  # 看透
        self.acupoint_seal_turns = 0  # 封穴
        self.shadow_clone_num = 0  # 影分身
        self.sixpaths_mode_turns = 0  # 六道模式
        self.is_soul_stealed = False  # 本回合是否被魂吸
        self.is_fatal_sealed = False  # 封尽
        self.is_in_kamui_zone = False  # 是否在神威空间
        # 招式选择参数
        self.selected_skill_id = -1
        # 看透招式选择参数
        self.charmed_by = -1
        self.preselected_skill_id = -1
        self.preselected_target_ids = []

    def __str__(self):
        return f"<玩家 {self.id}>"

    def print_status(self):
        print(self)
        
        if not self.is_available():
            print('已死亡', end='：')
            
            if self.is_fatal_sealed:
                print('已被尸鬼封尽', end='；')

            if self.is_in_kamui_zone:
                print('处于神威空间', end='；')
            
            print('')
            return
        
        print('查克拉:', self.mp, end='；')
        
        if not self.is_dead:
            print('本体生命值:', self.hp, '，本体生命上限', self.max_hp, end='；')
        
        if self.is_in_second_life:
            print('秽土状态，秽土生命值:', self.second_hp, '，秽土生命上限:', self.second_max_hp, end='；')
        
        if self.bind_turns:
            print('剩余束缚回合:', self.bind_turns, end='；')
        
        if self.is_exposed:
            print('被看透，预选招式:', self.preselected_skill_id, '，招式目标:', self.preselected_target_ids, end='；')
            if self.charmed_by != -1:
                print('被魅惑:', self.charmed_by, end='；')
            
        if self.acupoint_seal_turns:
            print('封穴剩余回合:', self.acupoint_seal_turns, end='；')

        if self.shadow_clone_num:
            print('影分身数量:', self.shadow_clone_num, end='；')

        if self.sixpaths_mode_turns:
            print('六道模式剩余回合:', self.sixpaths_mode_turns, end='；')

        if self.is_fatal_sealed:
            print('已被尸鬼封尽', end='；')

        if self.is_in_kamui_zone:
            print('处于神威空间', end='；')
        
        print('')

    def is_available(self) -> bool:
        """
        判断玩家是否仍有效（没有死过或者死亡后被秽土）

        Returns:
            bool: 是否有效
        """
        return not self.is_dead or self.is_dead and self.is_in_second_life

    def restore_mp(self, amount: int):
        """
        玩家回蓝

        Args:
            amount (int): 回复量
        """
        self.mp += amount
        print(f"{self} 回复了 {amount} 点查克拉，剩余：{self.mp}")
    
    def use_mp(self, amount: int):
        """
        玩家耗蓝

        Args:
            amount (int): 消量
        """
        self.mp -= amount
        if amount:
            print(f"{self} 消耗了 {amount} 点查克拉，剩余：{self.mp}")

    def clear_mp(self):
        """
        被魂吸
        """
        self.mp = 0
        print(f"{self} 被魂吸，查克拉清零")

    def restore_hp(self, amount: int):
        """
        玩家回血

        Args:
            amount (int): 回复量
        """
        if self.is_in_second_life:
            self.second_hp = min(self.second_hp + amount, self.second_max_hp)
            print(f"{self} 的秽土回复了 {amount} 点生命，剩余: {self.second_hp}")
        else:
            self.hp = min(self.hp + amount, self.max_hp)
            print(f"{self} 的本体回复了 {amount} 点生命，剩余：{self.hp}")

    def add_max_hp(self):
        """
        增加最大生命值，最多 6
        """
        if self.is_in_second_life:
            self.second_max_hp = 6
            print(f"{self} 的秽土最大生命值增加至 6 点")
        else:
            self.max_hp = 6
            print(f"{self} 的本体最大生命值增加至 6 点")

    def receive_damage(self, damage: int) -> int:
        """
        玩家受到伤害处理

        Args:
            damage (int): 球的伤害

        Returns:
            int: 实际造成伤害
        """
        if not self.is_available():
            return 0

        hp_before_damage = (
            self.second_hp if self.is_in_second_life else self.hp
        )  # 记录扣血前血量，用于计算实际伤害

        # 秽土扣血
        if self.is_in_second_life:
            self.second_hp -= damage
            print(f"{self} 的秽土受到了 {damage} 点伤害，剩余生命值: {self.second_hp}")

            if self.second_hp <= 0:
                self.is_in_second_life = False
                print(f"{self} 的秽土死亡")
        # 本体扣血
        else:
            self.hp -= damage
            print(f"{self} 的本体受到了 {damage} 点伤害，剩余生命值：{self.hp}")

            if self.hp <= 0:
                self.is_dead = True
                print(f"{self} 死亡")

        actual_damage = min(hp_before_damage, damage)
        return actual_damage

    def is_bound(self) -> bool:
        """
        是否被束缚

        Returns:
            bool: 是否被束缚
        """
        return self.bind_turns > 0

    def add_bind_turns(self, amount: int):
        """
        增减束缚回合
        """
        self.bind_turns = max(self.bind_turns + amount, 0)
        if amount > 0:
            print(f"{self} 被束缚，剩余束缚回合: {self.bind_turns}")

    def expose(self):
        """
        看透
        """
        self.is_exposed = True
        print(f'{self} 被看透')

    def is_acupoint_sealed(self) -> bool:
        """
        是否被封穴

        Returns:
            bool: 是否被封穴
        """
        return self.acupoint_seal_turns > 0

    def add_acupoint_seal_turns(self, amount: int):
        """
        增减封穴回合
        """
        self.acupoint_seal_turns = max(self.acupoint_seal_turns + amount, 0)
        if amount > 0:
            print(f"{self} 被封穴，剩余封穴回合: {self.acupoint_seal_turns}")

    def add_shadow_clone_num(self, amount: int):
        """
        增减影分身数量
        """
        self.shadow_clone_num = max(self.shadow_clone_num + amount, 0)
        if amount > 0:
            print(f"{self} 影分身数量增加，剩余影分身数量: {self.shadow_clone_num}")

    def is_in_sixpaths_mode(self) -> bool:
        """
        是否在六道模式

        Returns:
            bool: 是否在六道模式
        """
        return self.sixpaths_mode_turns > 0

    def add_sixpaths_mode_turns(self, amount: int):
        """
        增减六道模式回合数量
        """
        self.sixpaths_mode_turns = max(self.sixpaths_mode_turns + amount, 0)
        if amount > 0:
            print(f"{self} 进入六道模式，剩余六道回合: {self.sixpaths_mode_turns}")

    def fatal_seal(self):
        """
        尸鬼封禁
        """
        self.is_fatal_sealed = True

        if self.is_in_second_life:
            self.is_in_second_life = False
            print(f"{self} 的秽土被封禁")
        else:
            self.is_dead = True
            print(f"{self} 的本体被封禁，死亡")

    def is_able_to_reborn(self) -> bool:
        """
        是否能被秽土转生
        被尸鬼封尽过或者已经有一条秽土时不能被秽土转生

        Returns:
            bool: 是否能被秽土
        """
        return not self.is_fatal_sealed and not self.is_in_second_life

    def reanimation(self):
        """
        秽土转生
        """
        if not self.is_able_to_reborn():
            print(f"{self} 无法秽土，无效")
            return

        self.is_in_second_life = True
        self.second_hp = 2
        self.second_max_hp = 4

        if self.is_dead:
            self.mp = 0

    def switch_zone(self):
        """
        切换空间
        """
        self.is_in_kamui_zone = not self.is_in_kamui_zone
