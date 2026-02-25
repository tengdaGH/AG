'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

type Language = 'en' | 'zh';

type Translations = {
    [key in Language]: {
        [key: string]: string;
    };
};

const translations: Translations = {
    en: {
        // Landing Page
        'nav.itemBank': 'Item Bank',
        'nav.practiceSuite': 'Practice Suite',
        'nav.proctorDashboard': 'Proctor Dashboard',
        'home.setupComplete': 'Platform Foundation Setup Complete ✨',
        'home.title': 'Next-Generation Assessment',
        'home.lead': 'The centralized portal for item designers, psychometricians, and candidates to experience the adaptive, AI-scored English proficiency test.',
        'home.enterDashboard': 'Enter Dashboard',
        'home.itemBankTitle': '📝 Item Bank Builder',
        'home.itemBankDesc': 'Design and tag questions for Reading, Listening, Speaking, and Writing sections.',
        'home.aiScoringTitle': '🤖 AI Automated Scoring',
        'home.aiScoringDesc': 'Integrate NLP and Speech-to-Text models for instant, unbiased candidate evaluation.',
        'home.secureTitle': '🔒 Secure Proctoring',
        'home.secureDesc': 'Deploy the lockdown browser environment with zero-latency media streaming.',

        // Login Page
        'login.welcome': 'Welcome back',
        'login.subtitle': 'Sign in to the TOEFL 2026 Assessment Platform',
        'login.signInBtn': 'Sign In',
        'login.email': 'Email address',
        'login.password': 'Password',
        'login.roleLabel': 'Sign in as Role (Demo purposes)',
        'login.roleStudent': 'Test Taker (Student)',
        'login.roleAdmin': 'System Administrator',
        'login.roleRater': 'Human Rater / Scorer',
        'login.roleProctor': 'Test Center Proctor',
        'login.authenticating': 'Authenticating...',
        'login.noAccount': "Don't have an account?",
        'login.createAccount': 'Create an account',
        'login.action': 'Access Platform',

        // Student Dashboard
        'student.portal': 'Student Portal',
        'student.signOut': 'Sign Out',
        'student.myAssessments': 'My Assessments',
        'student.myAssessmentsDesc': 'View upcoming tests, practice modules, and past scores.',
        'student.upcoming': 'UPCOMING',
        'student.simulation': 'TOEFL iBT (Simulation)',
        'student.testDate': 'Test Date',
        'student.testDateDesc': 'Ensure you have an external microphone and a quiet room. The lockdown browser will secure your session 15 minutes prior to the start time.',
        'student.launchProctor': 'Launch Proctor Check-in',
        'student.speakingPractice': 'Speaking Practice Set 3',
        'student.practice': 'PRACTICE',
        'student.topic': 'Topic: Academic AI Impact',
        'student.practiceDesc': 'Answer 4 speaking tasks. Our fine-tuned NLP model will grade your pronunciation and fluency instantly.',
        'student.startPractice': 'Start Practice',
        'student.pastScores': 'Past Scores',
        'student.diagnosticTest': 'Diagnostic Test A',
        'student.totalScore': 'Total',
        'student.writingOnly': 'Writing Section Only',
        'student.viewAnalytics': 'View Analytics',

        // Admin Dashboard
        'admin.portal': 'Admin / Item Developer Portal',
        'admin.signOut': 'Sign Out',
        'admin.overview': 'Platform Overview',
        'admin.manageItemsTitle': 'Item Bank Management',
        'admin.manageItemsDesc': 'Active test items in the repository.',
        'admin.manageItemsBtn': 'Manage Items',
        'admin.createNewBtn': 'Create New',
        'admin.systemHealthTitle': 'System Health',
        'admin.dbOnline': 'PostgreSQL Database',
        'admin.aiOnline': 'AI Scoring Microservices',
        'admin.webrtcStatus': 'WebRTC Signaling',
        'admin.statusOnline': 'Online',
        'admin.statusDegraded': 'Degraded',
        'admin.userMgmtTitle': 'User Management',
        'admin.userMgmtDesc': 'Manage Students, Proctors, Raters, and internal platform access.',
        'admin.viewDirectoryBtn': 'View Directory',

        // Proctor Dashboard
        'proctor.portal': 'Live Proctor Dashboard',
        'proctor.endSession': 'End Session',
        'proctor.activeSession': 'Active Session ID: TS-992-11',
        'proctor.testCenter': 'Test Center 12A',
        'proctor.monitoring': 'Monitoring 45 active candidates.',
        'proctor.lockdownAll': 'Lockdown All Stations',
        'proctor.station04': 'Station 04',
        'proctor.candidate948112': 'Candidate ID: 948112',
        'proctor.aiFlag': 'AI Flag: Anomalous audio background noise detected.',
        'proctor.viewStream': 'View Stream',
        'proctor.pauseExam': 'Pause Exam',
        'proctor.station12': 'Station 12',
        'proctor.candidate991244': 'Candidate ID: 991244',
        'proctor.listening': 'Listening Section - Question 14',
        'proctor.station15': 'Station 15',
        'proctor.candidate991288': 'Candidate ID: 991288',
        'proctor.reading': 'Reading Section - Question 32',

        // Rater Dashboard
        'rater.portal': 'Human Rater Portal',
        'rater.signOut': 'Sign Out',
        'rater.expertRater': 'Expert Rater: Dr. Smith',
        'rater.queue': 'Scoring Queue',
        'rater.queueDesc': 'Review AI-flagged or randomly sampled essays and speaking audio for calibration.',
        'rater.speakingResponses': 'Speaking Responses',
        'rater.speakingPending': '14 PENDING',
        'rater.speakingDesc': 'Assess pronunciation, fluency, and topic development against the 2026 analytic rubrics. Automated AI scores pre-loaded.',
        'rater.startQueue': 'Start Queue',
        'rater.writingResponses': 'Writing Responses',
        'rater.writingPending': '2 PENDING',
        'rater.writingDesc': 'Review "Academic Discussion" essays. Verify AI plagiarism flags and cohesiveness.',
        'rater.reviewEssays': 'Review Essays',

        // Test Engine
        'test.readingSection': 'Reading Section',
        'test.listeningSection': 'Listening Section',
        'test.timeRemaining': 'Time Remaining',
        'test.question': 'Question',
        'test.connectionStable': 'Connection Stable',
        'test.submitSection': 'Submit Section',
        'test.next': 'Next',
        'test.back': 'Back',
        'test.readingCompleteAlert': 'Reading Section completed! Moving to the Listening Section.',
        'test.timeUpAlert': 'Time is up! Your responses have been auto-submitted.',
        'test.listeningStage1': 'Listening Section - Stage 1',
        'test.volumeCheck': 'Volume Check',
        'test.answeringTime': 'Answering Time',
        'test.playingAudio': 'Playing Audio...',
        'test.doNotRemoveHeadphones': 'Do not remove headphones',
        'test.academicLecture': 'Academic Lecture: History',
        'test.directionsListening': 'Directions: Listening Section',
        'test.listeningInstructions': 'You will now hear an academic lecture. You may take notes while you listen. You will not be able to hear the audio again. After the audio finishes, the answering timer will begin.',
        'test.testVolume': 'Test Volume',
        'test.beginLecture': 'Begin Lecture',
        'test.listenCarefully': 'Listen Carefully',
        'test.questionsAppearAuto': 'The questions will appear automatically when the lecture concludes.',
        'test.submitAndEnterStage2': 'Submit & Enter Stage 2 Next Block',
        'test.listeningCompleteAlert': 'Block 1 completed. Engine calculating 3PL IRT Theta...\nRouting candidate to Hard Stage 2 block.',

        // Speaking UI
        'test.speakingSectionVirtual': 'Speaking Section: Virtual Interview',
        'test.preparationTime': 'Preparation Time',
        'test.recordingActive': 'Recording Active',
        'test.task1Of2': 'Task 1 of 2',
        'test.listenToQuestion': 'Listen to the question carefully.',
        'test.speakPrepInstructions': 'You will have 15 seconds to prepare your response, and 45 seconds to speak.',
        'test.startTask': 'Start Task',
        'test.prepareResponse': 'Prepare Your Response',
        'test.recordingBeginsAuto': 'Recording will begin automatically when the timer reaches zero.',
        'test.recording': 'Recording...',
        'test.speakClearly': 'Please speak clearly into your microphone.',
        'test.responseRecorded': 'Response Recorded successfully.',
        'test.audioUploaded': 'Your audio has been uploaded and secured.',
        'test.processingAudio': 'AI Processing Audio...',
        'test.completeTest': 'Complete Test',
        'test.speakingCompletedAlert1': 'Speaking section completed! Audio graded by AI.\nBand Score:',
        'test.speakingCompletedAlert2': 'Navigating to Dashboard...',

        // Writing UI
        'test.writingSectionEmail': 'Writing Section: Write an Email',
        'test.underWordCountWarning': 'Your response is under the recommended 50 words. Are you sure you want to submit?',
        'test.writingCompletedAlert1': 'Email submitted & Graded by AI!\nBand Score:',
        'test.writingCompletedAlert2': 'Navigating to Dashboard...',
        'test.timeUpWritingAlert': 'Time is up! Auto-submitted & Graded by AI!\nBand Score:',
        'test.directions': 'Directions',
        'test.writingDirectionsBody': 'Read the scenario below. Then, write an email responding to the situation. You have 10 minutes. A strong response should be at least 50 words.',
        'test.scenario': 'Scenario',
        'test.scenarioBody': 'You are a student registered for a biology course. The professor recently announced that the midterm exam date has been moved forward by one week due to a scheduling conflict with a guest lecturer. This new date conflicts with a mandatory field trip for your geology class.',
        'test.task': 'Task',
        'test.taskBody': 'Write an email to your biology professor, Dr. Miller. In your email, you should:',
        'test.taskBullet1': 'Explain your situation regarding the geology field trip.',
        'test.taskBullet2': 'Ask for a possible solution (e.g., taking the exam early, submitting an alternative assignment).',
        'test.taskBullet3': 'Maintain a polite and professional tone appropriate for university correspondence.',
        'test.to': 'To:',
        'test.subject': 'Subject:',
        'test.emailSubject': 'Midterm Exam Scheduling Conflict',
        'test.emailPlaceholder': 'Start your email here...',
        'test.wordCountLabel': 'Word Count:',
        'test.recommendedWords': '(Recommended: 50+)',
        'test.submitResponse': 'Submit Response',
        'test.analyzingSubmissions': 'AI Analyzing Submissions...'
    },
    zh: {
        // Landing Page
        'nav.itemBank': '题库',
        'nav.practiceSuite': '练习套件',
        'nav.proctorDashboard': '监考控制台',
        'home.setupComplete': '平台基础设置完成 ✨',
        'home.title': '新一代评估测试',
        'home.lead': '为题库设计者、心理测量学家和考生提供适应性、人工智能评分的英语能力测试的集中门户体验。',
        'home.enterDashboard': '进入控制台',
        'home.itemBankTitle': '📝 题库构建器',
        'home.itemBankDesc': '为阅读、听力、口语和写作部分设计和标记问题。',
        'home.aiScoringTitle': '🤖 AI 自动评分',
        'home.aiScoringDesc': '集成 NLP 和语音转文本模型，实现即时、公正的考生评估。',
        'home.secureTitle': '🔒 安全监考',
        'home.secureDesc': '部署锁定浏览器环境，实现零延迟媒体流。',

        // Login Page
        'login.welcome': '欢迎回来',
        'login.subtitle': '登录 TOEFL 2026 评估平台',
        'login.signInBtn': '登 录',
        'login.email': '电子邮箱',
        'login.password': '密码',
        'login.roleLabel': '登录角色（演示）',
        'login.roleStudent': '考生 (Student)',
        'login.roleAdmin': '系统管理员 (Admin)',
        'login.roleRater': '人类评分员 (Rater)',
        'login.roleProctor': '考试中心监考员 (Proctor)',
        'login.authenticating': '认证中...',
        'login.noAccount': "还没有账号？",
        'login.createAccount': '创建一个账号',
        'login.action': '进入系统',

        // Student Dashboard
        'student.portal': '学生门户',
        'student.signOut': '退出登录',
        'student.myAssessments': '我的评估',
        'student.myAssessmentsDesc': '查看即将举行的考试、练习模块和过往成绩。',
        'student.upcoming': '即将开始',
        'student.simulation': 'TOEFL iBT (模拟)',
        'student.testDate': '考试日期',
        'student.testDateDesc': '请确保您配有外部麦克风并在安静的房间内。锁定浏览器将在开考前 15 分钟保护您的会话安全。',
        'student.launchProctor': '启动监考检查',
        'student.speakingPractice': '口语练习集 3',
        'student.practice': '练习',
        'student.topic': '主题：学术 AI 的影响',
        'student.practiceDesc': '回答 4 个口语任务。我们微调后的 NLP 模型将立即为您的发音和流利度评分。',
        'student.startPractice': '开始练习',
        'student.pastScores': '过往成绩',
        'student.diagnosticTest': '诊断测试 A',
        'student.totalScore': '总分',
        'student.writingOnly': '仅写作部分',
        'student.viewAnalytics': '查看分析',

        // Admin Dashboard
        'admin.portal': '管理员 / 题目开发人员门户',
        'admin.signOut': '退出登录',
        'admin.overview': '平台概览',
        'admin.manageItemsTitle': '题库管理',
        'admin.manageItemsDesc': '存储库中的活动测试题。',
        'admin.manageItemsBtn': '管理题目',
        'admin.createNewBtn': '创建新题目',
        'admin.systemHealthTitle': '系统健康状况',
        'admin.dbOnline': 'PostgreSQL 数据库',
        'admin.aiOnline': 'AI 评分微服务',
        'admin.webrtcStatus': 'WebRTC 信号',
        'admin.statusOnline': '在线',
        'admin.statusDegraded': '降级',
        'admin.userMgmtTitle': '用户管理',
        'admin.userMgmtDesc': '管理学生、监考员、评分员和内部平台访问权限。',
        'admin.viewDirectoryBtn': '查看目录',

        // Proctor Dashboard
        'proctor.portal': '实时监考台',
        'proctor.endSession': '结束会话',
        'proctor.activeSession': '活动会话 ID: TS-992-11',
        'proctor.testCenter': '测试中心 12A',
        'proctor.monitoring': '正在监控 45 名活跃考生。',
        'proctor.lockdownAll': '锁定所有站点',
        'proctor.station04': '位置 04',
        'proctor.candidate948112': '考生 ID: 948112',
        'proctor.aiFlag': 'AI 标记：检测到异常背景音频噪音。',
        'proctor.viewStream': '查看流',
        'proctor.pauseExam': '暂停考试',
        'proctor.station12': '位置 12',
        'proctor.candidate991244': '考生 ID: 991244',
        'proctor.listening': '听力部分 - 第 14 题',
        'proctor.station15': '位置 15',
        'proctor.candidate991288': '考生 ID: 991288',
        'proctor.reading': '阅读部分 - 第 32 题',

        // Rater Dashboard
        'rater.portal': '人类评分员门户',
        'rater.signOut': '退出登录',
        'rater.expertRater': '专家评分员：Dr. Smith',
        'rater.queue': '评分队列',
        'rater.queueDesc': '审核 AI 标记的或随机抽样的作文和口语录音进行校准。',
        'rater.speakingResponses': '口语回答',
        'rater.speakingPending': '14 个待处理',
        'rater.speakingDesc': '对照 2026 年分析量规评估发音、流利度和主题发展。预先加载自动 AI 分数。',
        'rater.startQueue': '开始队列',
        'rater.writingResponses': '写作回答',
        'rater.writingPending': '2 个待处理',
        'rater.writingDesc': '审核“学术讨论”作文。验证 AI 的剽窃标记和连贯性。',
        'rater.reviewEssays': '审核作文',

        // Test Engine
        'test.readingSection': '阅读部分',
        'test.listeningSection': '听力部分',
        'test.timeRemaining': '剩余时间',
        'test.question': '题目',
        'test.connectionStable': '网络连接稳定',
        'test.submitSection': '提交部分',
        'test.next': '下一题',
        'test.back': '上一题',
        'test.readingCompleteAlert': '阅读部分完成！正在进入听力部分。',
        'test.timeUpAlert': '时间到！您的作答已自动提交。',
        'test.listeningStage1': '听力部分 - 阶段 1',
        'test.volumeCheck': '音量检查',
        'test.answeringTime': '答题时间',
        'test.playingAudio': '播放音频中...',
        'test.doNotRemoveHeadphones': '请勿摘下耳机',
        'test.academicLecture': '学术讲座：历史',
        'test.directionsListening': '说明：听力部分',
        'test.listeningInstructions': '您现在将听到一段学术讲座。在聆听时可以做笔记。您将无法再次听到该音频。音频结束后，答题计时器将开始计时。',
        'test.testVolume': '测试音量',
        'test.beginLecture': '开始讲座',
        'test.listenCarefully': '仔细聆听',
        'test.questionsAppearAuto': '讲座结束后，题目将自动出现。',
        'test.submitAndEnterStage2': '提交并进入阶段 2',
        'test.listeningCompleteAlert': '区块 1 完成。引擎正在计算 3PL IRT Theta...\n正在将考生引导至高难度阶段 2 区块。',

        // Speaking UI
        'test.speakingSectionVirtual': '口语部分：虚拟面试',
        'test.preparationTime': '准备时间',
        'test.recordingActive': '正在录音',
        'test.task1Of2': '任务 1，共 2 个',
        'test.listenToQuestion': '请仔细听问题。',
        'test.speakPrepInstructions': '您将有 15 秒钟的准备时间和 45 秒钟的作答时间。',
        'test.startTask': '开始任务',
        'test.prepareResponse': '准备作答',
        'test.recordingBeginsAuto': '计时器归零后将自动开始录音。',
        'test.recording': '正在录音...',
        'test.speakClearly': '请对着麦克风清晰地说话。',
        'test.responseRecorded': '作答已成功录制。',
        'test.audioUploaded': '您的音频已上传并保护。',
        'test.processingAudio': 'AI 正在处理音频...',
        'test.completeTest': '完成测试',
        'test.speakingCompletedAlert1': '口语部分完成！音频已由 AI 评分。\n等级分数：',
        'test.speakingCompletedAlert2': '正在导航至控制台...',

        // Writing UI
        'test.writingSectionEmail': '写作部分：写一封电子邮件',
        'test.underWordCountWarning': '您的作答少于建议的 50 个词。您确定要提交吗？',
        'test.writingCompletedAlert1': '电子邮件已提交并由 AI 评分！\n等级分数：',
        'test.writingCompletedAlert2': '正在导航至控制台...',
        'test.timeUpWritingAlert': '时间到！已自动提交并由 AI 评分！\n等级分数：',
        'test.directions': '说明',
        'test.writingDirectionsBody': '阅读下面的情景。然后，写一封电子邮件回复该情况。您有 10 分钟的时间。一个好的回答应该至少有 50 个词。',
        'test.scenario': '情景',
        'test.scenarioBody': '您是一名注册了生物课程的学生。教授最近宣布，由于与客座讲师的日程冲突，期中考试日期提前了一周。这个新日期与您的地质学课程的强制性实地考察相冲突。',
        'test.task': '任务',
        'test.taskBody': '写一封电子邮件给您的生物学教授米勒博士。在您的电子邮件中，您应该：',
        'test.taskBullet1': '解释关于地质学实地考察的情况。',
        'test.taskBullet2': '寻求可能的解决方案（例如，提前参加考试，提交替代作业）。',
        'test.taskBullet3': '保持适合大学通信的礼貌和专业的语气。',
        'test.to': '收件人：',
        'test.subject': '主题：',
        'test.emailSubject': '期中考试日程冲突',
        'test.emailPlaceholder': '从这里开始写您的电子邮件...',
        'test.wordCountLabel': '字数计数：',
        'test.recommendedWords': '（建议：50+）',
        'test.submitResponse': '提交作答',
        'test.analyzingSubmissions': 'AI 正在分析提交内容...'
    }
};

interface LanguageContextType {
    language: Language;
    setLanguage: (lang: Language) => void;
    t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
    const [language, setLanguage] = useState<Language>('en');

    const t = (key: string) => {
        return translations[language][key] || key;
    };

    return (
        <LanguageContext.Provider value={{ language, setLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
}

export function useLanguage() {
    const context = useContext(LanguageContext);
    if (context === undefined) {
        throw new Error('useLanguage must be used within a LanguageProvider');
    }
    return context;
}
