import { DocumentItem, StudentProgress, TopicMastery, StudyPack, Quiz } from './types';

export const MOCK_DOCUMENTS: DocumentItem[] = [
  {
    id: 'doc_quantum_01',
    title: 'Quantum Mechanics — Wavefunctions & Schrödinger Dynamics',
    filename: 'principles_of_quantum_mechanics_ch1.pdf',
    file_size: 4194304,
    mime_type: 'application/pdf',
    status: 'READY',
    total_pages: 38,
    total_chunks: 142,
    word_count: 28400,
    topic_count: 5,
    summary:
      'Rigorous foundation of wave-particle duality, probability density interpretation, operators in Hilbert space, and time-dependent Schrödinger dynamics with boundary condition solutions.',
    topics: [
      {
        id: 'top_qm_01',
        name: 'Wave-Particle Duality & de Broglie Relation',
        difficulty_level: 'INTERMEDIATE',
        chunk_count: 24,
        mastery_score: 0.88,
        description: 'de Broglie hypothesis λ = h/p and electron diffraction experiments.'
      },
      {
        id: 'top_qm_02',
        name: 'Born Statistical Interpretation',
        difficulty_level: 'INTERMEDIATE',
        chunk_count: 32,
        mastery_score: 0.74,
        description: 'Physical meaning of |ψ|², normalization, and probability currents.'
      },
      {
        id: 'top_qm_03',
        name: 'Schrödinger Time-Dependent Equation',
        difficulty_level: 'ADVANCED',
        chunk_count: 48,
        mastery_score: 0.52,
        description: 'Derivation, Hamiltonian operator Hψ = iℏ ∂ψ/∂t, and phase evolution.'
      },
      {
        id: 'top_qm_04',
        name: 'Heisenberg Uncertainty Principle',
        difficulty_level: 'INTERMEDIATE',
        chunk_count: 20,
        mastery_score: 0.92,
        description: 'Commutator algebra [x, p] = iℏ and dispersion products Δx·Δp ≥ ℏ/2.'
      },
      {
        id: 'top_qm_05',
        name: 'Infinite Square Well & Boundary Conditions',
        difficulty_level: 'ADVANCED',
        chunk_count: 18,
        mastery_score: 0.44,
        description: 'Energy quantization, sinusoidal stationary states, and orthogonality.'
      }
    ],
    created_at: '2026-10-06T14:30:00Z',
    updated_at: '2026-10-06T15:10:00Z'
  },
  {
    id: 'doc_neural_02',
    title: 'Deep Learning Architectures — Attention & Transformers',
    filename: 'attention_is_all_you_need_annotated.pdf',
    file_size: 3254100,
    mime_type: 'application/pdf',
    status: 'READY',
    total_pages: 24,
    total_chunks: 98,
    word_count: 19800,
    topic_count: 4,
    summary:
      'In-depth study of scaled dot-product attention, multi-head projections, positional encodings, layer normalization, and autoregressive causal masking.',
    topics: [
      {
        id: 'top_dl_01',
        name: 'Scaled Dot-Product Attention',
        difficulty_level: 'INTERMEDIATE',
        chunk_count: 26,
        mastery_score: 0.81,
        description: 'Softmax(QK^T / sqrt(d_k))V mechanism and variance stabilization.'
      },
      {
        id: 'top_dl_02',
        name: 'Multi-Head Attention Projections',
        difficulty_level: 'ADVANCED',
        chunk_count: 28,
        mastery_score: 0.65,
        description: 'Parallel representation subspaces and parameter tensor concatenation.'
      },
      {
        id: 'top_dl_03',
        name: 'Sinusoidal Positional Encoding',
        difficulty_level: 'INTERMEDIATE',
        chunk_count: 20,
        mastery_score: 0.89,
        description: 'Trigonometric frequency embeddings to preserve sequence ordering.'
      },
      {
        id: 'top_dl_04',
        name: 'Layer Normalization & Residual Highways',
        difficulty_level: 'BEGINNER',
        chunk_count: 24,
        mastery_score: 0.95,
        description: 'Gradient propagation stability and activation variance control.'
      }
    ],
    created_at: '2026-10-05T09:15:00Z',
    updated_at: '2026-10-05T10:00:00Z'
  },
  {
    id: 'doc_thermo_03',
    title: 'Statistical Thermodynamics — Entropy & Partition Functions',
    filename: 'microstates_and_canonical_ensembles.docx',
    file_size: 1945600,
    mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    status: 'READY',
    total_pages: 18,
    total_chunks: 74,
    word_count: 14200,
    topic_count: 3,
    summary:
      'Boltzmann entropy equation, Canonical ensemble partition function Z = sum exp(-beta E_i), Helmholtz free energy, and equipartition theorem.',
    topics: [
      {
        id: 'top_th_01',
        name: 'Boltzmann Entropy Formula S = k_B ln Ω',
        difficulty_level: 'INTERMEDIATE',
        chunk_count: 22,
        mastery_score: 0.77,
        description: 'Microstate multiplicity and statistical origin of the Second Law.'
      },
      {
        id: 'top_th_02',
        name: 'Canonical Partition Function',
        difficulty_level: 'ADVANCED',
        chunk_count: 32,
        mastery_score: 0.38,
        description: 'Thermal weight summation and bridging microscopic states to macro variables.'
      },
      {
        id: 'top_th_03',
        name: 'Helmholtz Free Energy & Chemical Potential',
        difficulty_level: 'ADVANCED',
        chunk_count: 20,
        mastery_score: 0.50,
        description: 'F = -k_B T ln Z and spontaneous equilibrium conditions.'
      }
    ],
    created_at: '2026-10-04T18:40:00Z',
    updated_at: '2026-10-04T19:22:00Z'
  }
];

export const MOCK_PROGRESS: StudentProgress = {
  student_id: 'usr_figure_01',
  total_documents_studied: 8,
  total_learning_time_minutes: 420,
  current_streak_days: 7,
  total_quizzes_completed: 24,
  average_quiz_score: 87.5,
  mastery_distribution: {
    novice: 2,
    learning: 4,
    proficient: 6,
    mastered: 8
  },
  upcoming_reviews_count: 3
};

export const MOCK_TOPIC_MASTERY: TopicMastery[] = [
  {
    topic_id: 'top_qm_01',
    topic_name: 'Wave-Particle Duality & de Broglie Relation',
    document_id: 'doc_quantum_01',
    mastery_score: 0.88,
    confidence_level: 'HIGH',
    last_practiced_at: '2026-10-06T15:20:00Z',
    spaced_repetition_interval_days: 4,
    next_review_at: '2026-10-10T15:20:00Z',
    status: 'MASTERED'
  },
  {
    topic_id: 'top_qm_02',
    topic_name: 'Born Statistical Interpretation',
    document_id: 'doc_quantum_01',
    mastery_score: 0.74,
    confidence_level: 'MODERATE',
    last_practiced_at: '2026-10-06T14:40:00Z',
    spaced_repetition_interval_days: 2,
    next_review_at: '2026-10-08T14:40:00Z',
    status: 'PRACTICING'
  },
  {
    topic_id: 'top_qm_03',
    topic_name: 'Schrödinger Time-Dependent Equation',
    document_id: 'doc_quantum_01',
    mastery_score: 0.52,
    confidence_level: 'LOW',
    last_practiced_at: '2026-10-06T13:00:00Z',
    spaced_repetition_interval_days: 1,
    next_review_at: '2026-10-07T13:00:00Z',
    status: 'LEARNING'
  },
  {
    topic_id: 'top_th_02',
    topic_name: 'Canonical Partition Function',
    document_id: 'doc_thermo_03',
    mastery_score: 0.38,
    confidence_level: 'LOW',
    last_practiced_at: '2026-10-05T11:00:00Z',
    spaced_repetition_interval_days: 1,
    next_review_at: '2026-10-07T09:00:00Z',
    status: 'NOVICE'
  },
  {
    topic_id: 'top_qm_05',
    topic_name: 'Infinite Square Well & Boundary Conditions',
    document_id: 'doc_quantum_01',
    mastery_score: 0.44,
    confidence_level: 'LOW',
    last_practiced_at: '2026-10-05T16:30:00Z',
    spaced_repetition_interval_days: 1,
    next_review_at: '2026-10-07T10:00:00Z',
    status: 'LEARNING'
  }
];

export const MOCK_STUDY_PACKS: Record<string, StudyPack> = {
  doc_quantum_01: {
    id: 'pack_qm_master',
    document_id: 'doc_quantum_01',
    title: 'Quantum Mechanics — Comprehensive Study Pack',
    status: 'READY',
    summary:
      'This dossier condenses Chapter 1 of Principles of Quantum Mechanics. Key focus areas include wave-particle duality, mathematical formulation of stationary states, time-dependent Schrödinger dynamics, and Heisenberg uncertainty bounds.',
    pack_type: 'complete',
    formula_sheet: [
      {
        name: 'de Broglie Wavelength',
        formula: 'λ = h / p = 2πℏ / p',
        variables: 'h: Planck constant (6.626×10⁻³⁴ J·s), p: momentum (kg·m/s)'
      },
      {
        name: 'Time-Dependent Schrödinger Equation',
        formula: 'iℏ ∂ψ/∂t = Ĥψ = (-ℏ²/2m ∇² + V)ψ',
        variables: 'ℏ: reduced Planck constant, Ĥ: Hamiltonian operator, V: potential'
      },
      {
        name: 'Born Normalization Condition',
        formula: '∫ |ψ(x, t)|² dx = 1',
        variables: '|ψ|²: probability density, integrated over entire spatial domain'
      },
      {
        name: 'Heisenberg Uncertainty Relation',
        formula: 'σ_x · σ_p ≥ ℏ / 2',
        variables: 'σ_x: position standard deviation, σ_p: momentum standard deviation'
      },
      {
        name: 'Infinite Square Well Energy Levels',
        formula: 'E_n = (n² π² ℏ²) / (2 m L²)',
        variables: 'n: quantum number (1, 2, 3...), L: well width, m: particle mass'
      }
    ],
    flashcards: [
      {
        id: 'fc_1',
        front: 'What is the physical interpretation of |ψ(x,t)|² in wave mechanics?',
        back: 'The Born interpretation: |ψ(x,t)|² dx gives the probability of finding the particle in the spatial interval [x, x+dx] at time t.',
        topic: 'Wavefunctions'
      },
      {
        id: 'fc_2',
        front: 'Why must a physical wavefunction be square-integrable?',
        back: 'Because the total probability of finding the particle somewhere in the universe must equal exactly 1 (unity normalization).',
        topic: 'Boundary Conditions'
      },
      {
        id: 'fc_3',
        front: 'What causes the energy quantization in an infinite potential well?',
        back: 'The spatial confinement boundary conditions ψ(0)=0 and ψ(L)=0 force the wavenumber k to take only discrete values k_n = nπ/L.',
        topic: 'Stationary States'
      },
      {
        id: 'fc_4',
        front: 'Does the Heisenberg uncertainty relation arise from measuring instrument errors?',
        back: 'No. It is an intrinsic mathematical property of non-commuting operators and wave packet Fourier transforms ([x, p] = iℏ).',
        topic: 'Uncertainty Principle'
      }
    ],
    key_takeaways: [
      'Wave-particle duality is unified via de Broglie relation λ = h/p.',
      'The Schrödinger equation is linear, enabling quantum superposition of stationary eigenstates.',
      'Time evolution for an energy eigenstate simply multiplies the spatial state by phase factor e^(-iEt/ℏ).',
      'Uncertainty Δx·Δp ≥ ℏ/2 is a foundational theorem of Fourier transform conjugate variables.'
    ],
    sample_questions: [
      {
        question: 'Prove that the probability current density J = (ℏ/2mi) (ψ* ∇ψ - ψ ∇ψ*) satisfies the continuity equation ∂ρ/∂t + ∇·J = 0.',
        answer: 'Differentiate ρ = ψ*ψ with respect to t and substitute iℏ ∂ψ/∂t = -ℏ²/2m ∇²ψ + Vψ and its complex conjugate. The potential terms cancel.'
      },
      {
        question: 'What is the ground state energy of an electron (m = 9.11×10⁻³¹ kg) in a 1 nm infinite well?',
        answer: 'E₁ = π²ℏ² / (2m L²) ≈ 0.376 eV.'
      }
    ],
    pdf_available: true,
    pdf_url: '/api/study-packs/pack_qm_master/pdf',
    pdf_size_bytes: 1420800,
    generated_at: '2026-10-06T15:30:00Z'
  }
};

export const MOCK_QUIZ: Quiz = {
  quiz_id: 'quiz_qm_interactive',
  document_id: 'doc_quantum_01',
  total_questions: 4,
  questions: [
    {
      id: 'q_01',
      type: 'mcq',
      topic_id: 'top_qm_01',
      prompt: 'According to the de Broglie hypothesis, what happens to the wavelength of an electron if its linear momentum is doubled?',
      options: [
        { key: 'A', text: 'The wavelength is doubled' },
        { key: 'B', text: 'The wavelength is halved' },
        { key: 'C', text: 'The wavelength quadruples' },
        { key: 'D', text: 'The wavelength remains constant' }
      ],
      model_answer: 'B',
      explanation:
        'Since λ = h / p, wavelength is inversely proportional to momentum. Doubling momentum halves the wavelength.'
    },
    {
      id: 'q_02',
      type: 'mcq',
      topic_id: 'top_qm_02',
      prompt: 'Under the Born statistical interpretation, what condition must any physically valid quantum state ψ(x) satisfy?',
      options: [
        { key: 'A', text: 'The integral ∫ |ψ(x)|² dx must equal 1 over all space' },
        { key: 'B', text: 'The derivative dψ/dx must be zero at all boundaries' },
        { key: 'C', text: 'The wavefunction must be purely real numbers with no imaginary part' },
        { key: 'D', text: 'The wavefunction must oscillate at lightspeed' }
      ],
      model_answer: 'A',
      explanation:
        'The Born rule requires normalization: the total probability of finding the particle somewhere in space is unity.'
    },
    {
      id: 'q_03',
      type: 'short_answer',
      topic_id: 'top_qm_03',
      prompt: 'State the physical significance of the imaginary unit i in the time-dependent Schrödinger equation iℏ ∂ψ/∂t = Ĥψ.',
      model_answer: 'The imaginary unit i allows oscillatory phase evolution (unitary dynamics) without exponential amplitude decay.',
      explanation:
        'The factor of i ensures that the time evolution operator U(t) = exp(-iHt/ℏ) is unitary, preserving normalization of total probability.'
    },
    {
      id: 'q_04',
      type: 'conceptual',
      topic_id: 'top_qm_04',
      prompt: 'Why does a localized wave packet with very small spatial uncertainty Δx necessarily have high momentum dispersion Δp?',
      model_answer: 'Position and momentum are Fourier transform conjugate pairs; localizing a function in space requires a wide superposition of spatial frequencies.',
      explanation:
        'Because [x, p] = iℏ, their spectral variances satisfy Δx·Δp ≥ ℏ/2. Narrowing in position requires adding higher frequency Fourier components.'
    }
  ]
};
