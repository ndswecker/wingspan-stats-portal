# portal/views/__init__.py

from .home import home

from .games import (
    GameCreateView,
    game_detail,
    game_edit,
    confirm_game_result_view,
)

from .friendship import (
    friends,
    send_friend_request_view,
    accept_friend_request_view,
    remove_friend_view,
    cancel_friend_request_view,
    decline_friend_request_view,
)

from .account import (
    account,
    register,
)

from .players import (
    competitive_history,
    player_overview,
    player_score_trends,
)

from .feathered_foe import (
    feathered_foe,
)

from .research import (
    research_home,
    turn_order_research,
    execute_turn_order_hypothesis,
)