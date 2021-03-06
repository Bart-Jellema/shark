from shark.base import  Enumeration, Object, Default, StringParam, BaseParamConverter
from shark.common import LOREM_IPSUM
from shark.objects.base import Raw
from shark.objects.layout import Paragraph, multiple_div_row
from shark.objects.text import Br
from shark.param_converters import IntegerParam, BooleanParam


def icon(name, size=0,
         fixed_width=False,
         border=False,
         pull_left=False,
         pull_right=False,
         spin=False,
         pulse=False,
         rotate=0,
         flip_horizontal=False,
         flip_vertical=False
         ):
    extra = ''
    if size:        extra += ' fa-{}'.format(['lg', '2x', '3x', '4x', '5x'][size])
    if fixed_width: extra += ' fa-fw'
    if border:      extra += ' fa-border'
    if pull_left:   extra += ' fa-pull-left'
    if pull_right:  extra += ' fa-pull-right'
    if pull_right:  extra += ' fa-spin'
    if pull_right:  extra += ' fa-pulse'
    if rotate in [90, 180, 270]: extra += ' fa-rotate-{}'.format(rotate)
    if flip_horizontal:  extra += ' fa-flip-horizontal'
    if flip_vertical:  extra += ' fa-flip-vertical'

    if isinstance(name, int):
        name = Icon.name(name)
    return Raw('<span class="fa fa-' + name.strip('_').replace('_', '-') + '{}"></span>'.format(extra))


class IconParam(BaseParamConverter):
    @classmethod
    def convert(cls, value, parent_object):
        if value is None or isinstance(value, Icon):
            return value
        elif isinstance(value, int):
            return Icon(Icon.name(value))
        elif str(value) in Icon.str_map:
            try:
                return Icon(value)
            except ValueError:
                pass

        raise TypeError('Parameter isn\'t of type int (Icon.???)')


class Icon(Object, Enumeration):
    """
    Icon from Font Awesome
    See the [Font Awesome documentation](http://fontawesome.io/examples/) on ideas of how and where to use the various options.
    """
    def __init__(self, name=Default, size=0,
                 fixed_width=False,
                 border=False,
                 pull_left=False,
                 pull_right=False,
                 spin=False,
                 pulse=False,
                 rotate=0,
                 flip_horizontal=False,
                 flip_vertical=False,
                 inverse=False,
                 stacked_on=None,
                 stacked_on_top=False, **kwargs):

        if isinstance(name, int):
            name = Icon.name(name)

        self.init(kwargs)
        self.name = self.param(name, StringParam, 'Name of the Font Awesome icon or you can use it like this: Icon.camera_retro', Icon.square)
        self.size = self.param(size, IntegerParam, 'Size of the icon. 1=33% larger, 2=2x the size, 3=3x the size, until 5x')
        self.fixed_width = self.param(fixed_width, BooleanParam, 'Fixed width icons for use in places like menus')
        self.border = self.param(border, BooleanParam, 'Add a rounded border around the icon')
        self.pull_left = self.param(pull_left, BooleanParam, 'Pull left. Useful for paragraph icons')
        self.pull_right = self.param(pull_right, BooleanParam, 'Pull left. Useful for paragraph icons')
        self.spin = self.param(spin, BooleanParam, 'Spin the icon. Great for use with `spinner`, `circle-o-notch`, `refresh` and `cog`')
        self.pulse = self.param(pulse, BooleanParam, 'Spin the icon in 8 steps')
        self.rotate = self.param(rotate, BooleanParam, 'Rotate the icon 90, 180 or 270 degrees. Other values are ignored.')
        self.flip_horizontal = self.param(flip_horizontal, BooleanParam, 'Flip the icon horizontally')
        self.flip_vertical = self.param(flip_vertical, BooleanParam, 'Flip the icon vertically')
        self.inverse = self.param(inverse, BooleanParam, 'Use an alternate icon color. Useful when stacking icons.')
        self.stacked_on = self.param(stacked_on, IconParam, 'Stack the icon on top of this icon. See example.')
        self.stacked_on_top = self.param(stacked_on_top, BooleanParam, 'Stack the larger icon on top of the smaller. Useful for icons like `ban`')

    def get_html(self, html):
        html.add_resource('https://maxcdn.bootstrapcdn.com/font-awesome/4.5.0/css/font-awesome.min.css', 'css',
                          'font-awesome', 'main')

        def get_extra(the_icon):
            extra = ''
            extra_icon = ''
            if self.size:        extra += ' fa-{}'.format(['lg', '2x', '3x', '4x', '5x'][self.size-1])
            if the_icon.fixed_width: extra += ' fa-fw'
            if the_icon.border:      extra += ' fa-border'
            if the_icon.pull_left:   extra += ' fa-pull-left'
            if the_icon.pull_right:  extra += ' fa-pull-right'
            if the_icon.spin:        extra_icon += ' fa-spin'
            if the_icon.pulse:       extra_icon += ' fa-pulse'
            if the_icon.rotate in [90, 180, 270]: extra_icon += ' fa-rotate-{}'.format(self.rotate)
            if the_icon.flip_horizontal:  extra_icon += ' fa-flip-horizontal'
            if the_icon.flip_vertical:  extra_icon += ' fa-flip-vertical'
            if the_icon.inverse:     extra_icon += ' fa-inverse'
            return extra, extra_icon

        if not self.stacked_on:
            self.add_class('fa fa-' + self.name.strip('_').replace('_', '-'))
            self.add_class(''.join(get_extra(self)))
            html.append('<span' + self.base_attributes + '></span>')
        else:
            if not isinstance(self.stacked_on, Icon):
                self.stacked_on = Icon(self.stacked_on)
            self.add_class('fa-stack')
            self.add_class(get_extra(self)[0])
            html.append('<span' + self.base_attributes + '>')
            small_icon = '    <span class="fa fa-stack-1x fa-' + self.name.strip('_').replace('_', '-') + '{}"></span>'.format(get_extra(self)[1])
            self.stacked_on.add_class('fa fa-stack-2x fa-' + self.stacked_on.name.strip('_').replace('_', '-'))
            self.stacked_on.add_class(get_extra(self.stacked_on)[1])
            large_icon = '    <span' + self.stacked_on.base_attributes + '></span>'

            if self.stacked_on_top:
                html.append(small_icon)
                html.append(large_icon)
            else:
                html.append(large_icon)
                html.append(small_icon)
            html.append('</span>')

    @classmethod
    def example(cls):
        return multiple_div_row([
            Icon('comments', 1, fixed_width=True), 'Just an icon, there are 605 available.', Br(),
            Icon('rocket', 1, spin=True, fixed_width=True), 'Icon spinning', Br(),
            Icon('spinner', 1, pulse=True, fixed_width=True), 'Icon with pulse', Br(),
            Icon(Icon.cc_amex, 1, fixed_width=True), 'Using the Icon.* enumeration to select the icon. Useful with code completion', Br(),
            Icon('hand_paper_o', 1, rotate=270, fixed_width=True), 'Rotated 270 degrees', Br(),
            Icon('line_chart', 1, flip_horizontal=True, fixed_width=True), 'Flipped', Br(),

            # Some examples of stacked icons
            Icon('flag', inverse=True, stacked_on='circle'), 'Simple stacked icons', Br(),
            Icon(Icon.terminal, inverse=True, stacked_on=Icon('square')), 'Stacked icon can be just the name or an actual Icon', Br(),
            Icon('camera', stacked_on=Icon('ban', classes='text-danger'), stacked_on_top=True), 'Another example', Br()
        ], [
            Paragraph([
                Icon('quote_left', 2, border=True, pull_left=True),
                LOREM_IPSUM
            ])
        ])

    adjust = 21
    anchor = 22
    archive = 23
    area_chart = 24
    arrows = 25
    arrows_h = 26
    arrows_v = 27
    asterisk = 28
    at = 29
    automobile = 30
    balance_scale = 31
    ban = 32
    bank = 33
    bar_chart = 34
    bar_chart_o = 35
    barcode = 36
    bars = 37
    battery_0 = 38
    battery_1 = 39
    battery_2 = 40
    battery_3 = 41
    battery_4 = 42
    battery_empty = 43
    battery_full = 44
    battery_half = 45
    battery_quarter = 46
    battery_three_quarters = 47
    bed = 48
    beer = 49
    bell = 50
    bell_o = 51
    bell_slash = 52
    bell_slash_o = 53
    bicycle = 54
    binoculars = 55
    birthday_cake = 56
    bluetooth = 57
    bluetooth_b = 58
    bolt = 59
    bomb = 60
    book = 61
    bookmark = 62
    bookmark_o = 63
    briefcase = 64
    bug = 65
    building = 66
    building_o = 67
    bullhorn = 68
    bullseye = 69
    bus = 70
    cab = 71
    calculator = 72
    calendar = 73
    calendar_check_o = 74
    calendar_minus_o = 75
    calendar_o = 76
    calendar_plus_o = 77
    calendar_times_o = 78
    camera = 79
    camera_retro = 80
    car = 81
    caret_square_o_down = 82
    caret_square_o_left = 83
    caret_square_o_right = 84
    caret_square_o_up = 85
    cart_arrow_down = 86
    cart_plus = 87
    cc = 88
    certificate = 89
    check = 90
    check_circle = 91
    check_circle_o = 92
    check_square = 93
    check_square_o = 94
    child = 95
    circle = 96
    circle_o = 97
    circle_o_notch = 98
    circle_thin = 99
    clock_o = 100
    clone = 101
    close = 102
    cloud = 103
    cloud_download = 104
    cloud_upload = 105
    code = 106
    code_fork = 107
    coffee = 108
    cog = 109
    cogs = 110
    comment = 111
    comment_o = 112
    commenting = 113
    commenting_o = 114
    comments = 115
    comments_o = 116
    compass = 117
    copyright = 118
    creative_commons = 119
    credit_card = 120
    credit_card_alt = 121
    crop = 122
    crosshairs = 123
    cube = 124
    cubes = 125
    cutlery = 126
    dashboard = 127
    database = 128
    desktop = 129
    diamond = 130
    dot_circle_o = 131
    download = 132
    edit = 133
    ellipsis_h = 134
    ellipsis_v = 135
    envelope = 136
    envelope_o = 137
    envelope_square = 138
    eraser = 139
    exchange = 140
    exclamation = 141
    exclamation_circle = 142
    exclamation_triangle = 143
    external_link = 144
    external_link_square = 145
    eye = 146
    eye_slash = 147
    eyedropper = 148
    fax = 149
    feed = 150
    female = 151
    fighter_jet = 152
    file_archive_o = 153
    file_audio_o = 154
    file_code_o = 155
    file_excel_o = 156
    file_image_o = 157
    file_movie_o = 158
    file_pdf_o = 159
    file_photo_o = 160
    file_picture_o = 161
    file_powerpoint_o = 162
    file_sound_o = 163
    file_video_o = 164
    file_word_o = 165
    file_zip_o = 166
    film = 167
    filter = 168
    fire = 169
    fire_extinguisher = 170
    flag = 171
    flag_checkered = 172
    flag_o = 173
    flash = 174
    flask = 175
    folder = 176
    folder_o = 177
    folder_open = 178
    folder_open_o = 179
    frown_o = 180
    futbol_o = 181
    gamepad = 182
    gavel = 183
    gear = 184
    gears = 185
    gift = 186
    glass = 187
    globe = 188
    graduation_cap = 189
    group = 190
    hand_grab_o = 191
    hand_lizard_o = 192
    hand_paper_o = 193
    hand_peace_o = 194
    hand_pointer_o = 195
    hand_rock_o = 196
    hand_scissors_o = 197
    hand_spock_o = 198
    hand_stop_o = 199
    hashtag = 200
    hdd_o = 201
    headphones = 202
    heart = 203
    heart_o = 204
    heartbeat = 205
    history = 206
    home = 207
    hotel = 208
    hourglass = 209
    hourglass_1 = 210
    hourglass_2 = 211
    hourglass_3 = 212
    hourglass_end = 213
    hourglass_half = 214
    hourglass_o = 215
    hourglass_start = 216
    i_cursor = 217
    image = 218
    inbox = 219
    industry = 220
    info = 221
    info_circle = 222
    institution = 223
    key = 224
    keyboard_o = 225
    language = 226
    laptop = 227
    leaf = 228
    legal = 229
    lemon_o = 230
    level_down = 231
    level_up = 232
    life_bouy = 233
    life_buoy = 234
    life_ring = 235
    life_saver = 236
    lightbulb_o = 237
    line_chart = 238
    location_arrow = 239
    lock = 240
    magic = 241
    magnet = 242
    mail_forward = 243
    mail_reply = 244
    mail_reply_all = 245
    male = 246
    map = 247
    map_marker = 248
    map_o = 249
    map_pin = 250
    map_signs = 251
    meh_o = 252
    microphone = 253
    microphone_slash = 254
    minus = 255
    minus_circle = 256
    minus_square = 257
    minus_square_o = 258
    mobile = 259
    mobile_phone = 260
    money = 261
    moon_o = 262
    mortar_board = 263
    motorcycle = 264
    mouse_pointer = 265
    music = 266
    navicon = 267
    newspaper_o = 268
    object_group = 269
    object_ungroup = 270
    paint_brush = 271
    paper_plane = 272
    paper_plane_o = 273
    paw = 274
    pencil = 275
    pencil_square = 276
    pencil_square_o = 277
    percent = 278
    phone = 279
    phone_square = 280
    photo = 281
    picture_o = 282
    pie_chart = 283
    plane = 284
    plug = 285
    plus = 286
    plus_circle = 287
    plus_square = 288
    plus_square_o = 289
    power_off = 290
    print = 291
    puzzle_piece = 292
    qrcode = 293
    question = 294
    question_circle = 295
    quote_left = 296
    quote_right = 297
    random = 298
    recycle = 299
    refresh = 300
    registered = 301
    remove = 302
    reorder = 303
    reply = 304
    reply_all = 305
    retweet = 306
    road = 307
    rocket = 308
    rss = 309
    rss_square = 310
    search = 311
    search_minus = 312
    search_plus = 313
    send = 314
    send_o = 315
    server = 316
    share = 317
    share_alt = 318
    share_alt_square = 319
    share_square = 320
    share_square_o = 321
    shield = 322
    ship = 323
    shopping_bag = 324
    shopping_basket = 325
    shopping_cart = 326
    sign_in = 327
    sign_out = 328
    signal = 329
    sitemap = 330
    sliders = 331
    smile_o = 332
    soccer_ball_o = 333
    sort = 334
    sort_alpha_asc = 335
    sort_alpha_desc = 336
    sort_amount_asc = 337
    sort_amount_desc = 338
    sort_asc = 339
    sort_desc = 340
    sort_down = 341
    sort_numeric_asc = 342
    sort_numeric_desc = 343
    sort_up = 344
    space_shuttle = 345
    spinner = 346
    spoon = 347
    square = 348
    square_o = 349
    star = 350
    star_half = 351
    star_half_empty = 352
    star_half_full = 353
    star_half_o = 354
    star_o = 355
    sticky_note = 356
    sticky_note_o = 357
    street_view = 358
    suitcase = 359
    sun_o = 360
    support = 361
    tablet = 362
    tachometer = 363
    tag = 364
    tags = 365
    tasks = 366
    taxi = 367
    television = 368
    terminal = 369
    thumb_tack = 370
    thumbs_down = 371
    thumbs_o_down = 372
    thumbs_o_up = 373
    thumbs_up = 374
    ticket = 375
    times = 376
    times_circle = 377
    times_circle_o = 378
    tint = 379
    toggle_down = 380
    toggle_left = 381
    toggle_off = 382
    toggle_on = 383
    toggle_right = 384
    toggle_up = 385
    trademark = 386
    trash = 387
    trash_o = 388
    tree = 389
    trophy = 390
    truck = 391
    tty = 392
    tv = 393
    umbrella = 394
    university = 395
    unlock = 396
    unlock_alt = 397
    unsorted = 398
    upload = 399
    user = 400
    user_plus = 401
    user_secret = 402
    user_times = 403
    users = 404
    video_camera = 405
    volume_down = 406
    volume_off = 407
    volume_up = 408
    warning = 409
    wheelchair = 410
    wifi = 411
    wrench = 412
    hand_o_down = 415
    hand_o_left = 416
    hand_o_right = 417
    hand_o_up = 418
    ambulance = 430
    subway = 442
    train = 444
    genderless = 447
    intersex = 448
    mars = 449
    mars_double = 450
    mars_stroke = 451
    mars_stroke_h = 452
    mars_stroke_v = 453
    mercury = 454
    neuter = 455
    transgender = 456
    transgender_alt = 457
    venus = 458
    venus_double = 459
    venus_mars = 460
    file = 461
    file_o = 468
    file_text = 474
    file_text_o = 475
    cc_amex = 495
    cc_diners_club = 496
    cc_discover = 497
    cc_jcb = 498
    cc_mastercard = 499
    cc_paypal = 500
    cc_stripe = 501
    cc_visa = 502
    google_wallet = 505
    paypal = 506
    bitcoin = 512
    btc = 513
    cny = 514
    dollar = 515
    eur = 516
    euro = 517
    gbp = 518
    gg = 519
    gg_circle = 520
    ils = 521
    inr = 522
    jpy = 523
    krw = 524
    rmb = 526
    rouble = 527
    rub = 528
    ruble = 529
    rupee = 530
    shekel = 531
    sheqel = 532
    try_ = 533
    turkish_lira = 534
    usd = 535
    won = 536
    yen = 537
    align_center = 538
    align_justify = 539
    align_left = 540
    align_right = 541
    bold = 542
    chain = 543
    chain_broken = 544
    clipboard = 545
    columns = 546
    copy = 547
    cut = 548
    dedent = 549
    files_o = 555
    floppy_o = 556
    font = 557
    header = 558
    indent = 559
    italic = 560
    link = 561
    list = 562
    list_alt = 563
    list_ol = 564
    list_ul = 565
    outdent = 566
    paperclip = 567
    paragraph = 568
    paste = 569
    repeat = 570
    rotate_left = 571
    rotate_right = 572
    save = 573
    scissors = 574
    strikethrough = 575
    subscript = 576
    superscript = 577
    table = 578
    text_height = 579
    text_width = 580
    th = 581
    th_large = 582
    th_list = 583
    underline = 584
    undo = 585
    unlink = 586
    angle_double_down = 587
    angle_double_left = 588
    angle_double_right = 589
    angle_double_up = 590
    angle_down = 591
    angle_left = 592
    angle_right = 593
    angle_up = 594
    arrow_circle_down = 595
    arrow_circle_left = 596
    arrow_circle_o_down = 597
    arrow_circle_o_left = 598
    arrow_circle_o_right = 599
    arrow_circle_o_up = 600
    arrow_circle_right = 601
    arrow_circle_up = 602
    arrow_down = 603
    arrow_left = 604
    arrow_right = 605
    arrow_up = 606
    arrows_alt = 608
    caret_down = 611
    caret_left = 612
    caret_right = 613
    caret_up = 618
    chevron_circle_down = 619
    chevron_circle_left = 620
    chevron_circle_right = 621
    chevron_circle_up = 622
    chevron_down = 623
    chevron_left = 624
    chevron_right = 625
    chevron_up = 626
    long_arrow_down = 632
    long_arrow_left = 633
    long_arrow_right = 634
    long_arrow_up = 635
    backward = 641
    compress = 642
    eject = 643
    expand = 644
    fast_backward = 645
    fast_forward = 646
    forward = 647
    pause = 648
    pause_circle = 649
    pause_circle_o = 650
    play = 651
    play_circle = 652
    play_circle_o = 653
    step_backward = 655
    step_forward = 656
    stop = 657
    stop_circle = 658
    stop_circle_o = 659
    youtube_play = 660
    _500px = 661
    adn = 662
    amazon = 663
    android = 664
    angellist = 665
    apple = 666
    behance = 667
    behance_square = 668
    bitbucket = 669
    bitbucket_square = 670
    black_tie = 672
    buysellads = 676
    chrome = 685
    codepen = 686
    codiepie = 687
    connectdevelop = 688
    contao = 689
    css3 = 690
    dashcube = 691
    delicious = 692
    deviantart = 693
    digg = 694
    dribbble = 695
    dropbox = 696
    drupal = 697
    edge = 698
    empire = 699
    expeditedssl = 700
    facebook = 701
    facebook_f = 702
    facebook_official = 703
    facebook_square = 704
    firefox = 705
    flickr = 706
    fonticons = 707
    fort_awesome = 708
    forumbee = 709
    foursquare = 710
    ge = 711
    get_pocket = 712
    git = 715
    git_square = 716
    github = 717
    github_alt = 718
    github_square = 719
    gittip = 720
    google = 721
    google_plus = 722
    google_plus_square = 723
    gratipay = 725
    hacker_news = 726
    houzz = 727
    html5 = 728
    instagram = 729
    internet_explorer = 730
    ioxhost = 731
    joomla = 732
    jsfiddle = 733
    lastfm = 734
    lastfm_square = 735
    leanpub = 736
    linkedin = 737
    linkedin_square = 738
    linux = 739
    maxcdn = 740
    meanpath = 741
    medium = 742
    mixcloud = 743
    modx = 744
    odnoklassniki = 745
    odnoklassniki_square = 746
    opencart = 747
    openid = 748
    opera = 749
    optin_monster = 750
    pagelines = 751
    pied_piper = 753
    pied_piper_alt = 754
    pinterest = 755
    pinterest_p = 756
    pinterest_square = 757
    product_hunt = 758
    qq = 759
    ra = 760
    rebel = 761
    reddit = 762
    reddit_alien = 763
    reddit_square = 764
    renren = 765
    safari = 766
    scribd = 767
    sellsy = 768
    shirtsinbulk = 771
    simplybuilt = 772
    skyatlas = 773
    skype = 774
    slack = 775
    slideshare = 776
    soundcloud = 777
    spotify = 778
    stack_exchange = 779
    stack_overflow = 780
    steam = 781
    steam_square = 782
    stumbleupon = 783
    stumbleupon_circle = 784
    tencent_weibo = 785
    trello = 786
    tripadvisor = 787
    tumblr = 788
    tumblr_square = 789
    twitch = 790
    twitter = 791
    twitter_square = 792
    usb = 793
    viacoin = 794
    vimeo = 795
    vimeo_square = 796
    vine = 797
    vk = 798
    wechat = 799
    weibo = 800
    weixin = 801
    whatsapp = 802
    wikipedia_w = 803
    windows = 804
    wordpress = 805
    xing = 806
    xing_square = 807
    y_combinator = 808
    y_combinator_square = 809
    yahoo = 810
    yc = 811
    yc_square = 812
    yelp = 813
    youtube = 814
    youtube_square = 816
    h_square = 818
    hospital_o = 822
    medkit = 823
    stethoscope = 825
    user_md = 826

