create table steamGameID
(
    appid int          not null
        primary key,
    name  varchar(300) null
);

create table steamGameInfo
(
    seq             int auto_increment
        primary key,
    appid           int          not null,
    is_free         tinyint(1)   null comment '무료여부',
    recommendations int          null comment '게임설명',
    release_date    datetime     null comment '출시일',
    release_status  tinyint(1)   null comment '출시여부',
    score           int          null comment '점수',
    price           varchar(250) null comment '평가',
    age             int          null comment '연령',
    constraint steamGameInfo_ibfk_1
        foreign key (appid) references steamGameID (appid)
);

create table steamGameInfo
(
    seq     int auto_increment primary key ,
    appid           int          not null,
    is_free         tinyint(1)   null comment '무료여부',
    recommendations int          null comment '게임설명',
    release_date    datetime     null comment '출시일',
    release_status  tinyint(1)   null comment '출시여부',
    score           int          null comment '점수',
    price           varchar(250) null comment '평가',
    age             int          null comment '연령',
    foreign key (appid) references steamGameID(appid)
);

create table steamGameReview
(
    seq                         int auto_increment
        primary key,
    appid   int not null ,
    recommend_id                int        null comment '추천 ID',
    review                      text       null comment '리뷰',
    timestamp_created           timestamp  null comment '리뷰 작성일',
    timestamp_updated           timestamp  null comment '리뷰 업데이트',
    voted_up                    tinyint(1) null comment '추천여부',
    votes_up                    int        null comment '리뷰 추천수',
    weighted_vote_score         float      null comment '유용성점수',
    received_for_free           tinyint(1) null comment '무료구매 여부',
    written_during_early_access tinyint(1) null comment '얼리 리뷰',
    constraint recommend_id
        unique (recommend_id),
        foreign key (appid) references steamGameID(appid)
);

create table steamUserToGameInfo
(
    seq                int auto_increment
        primary key,
    recommend_id       int           null comment '추천 ID',
    steam_id           varchar(1000) null comment '작성자 ID',
    playtime_forever   int           null comment '평생 플레이타임',
    playtime_two       int           null comment '2주간 플레이시간',
    playtime_at_review int           null comment '리뷰작성시 플레이타임',
    last_played        int           null comment '마지막 플레이 시간',
    constraint steamUserToGameInfo_ibfk_1
        foreign key (recommend_id) references steamGameReview (recommend_id)
);



