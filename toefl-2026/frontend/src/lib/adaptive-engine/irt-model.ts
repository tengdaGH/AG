/**
 * Item Response Theory (IRT) - 3 Parameter Logistic Model (3PL)
 * 
 * Used for the new 2026 Adaptive Reading and Listening sections.
 * This model calculates the probability of a candidate answering a question correctly.
 */

export interface TestItem {
    id: string;
    difficulty: number;      // b-parameter: How hard the question is (-3.0 to +3.0)
    discrimination: number;  // a-parameter: How well the question differentiates ability (0.5 to 2.5)
    guessing: number;        // c-parameter: Probability of guessing correctly (0 to 0.25 for 4-option MCQs)
}

export interface CandidateAbility {
    theta: number;           // Current estimated ability level (-3.0 to +3.0)
    standardError: number;   // Confidence in the current theta estimate
}

/**
 * Calculates the probability of a correct response based on the 3PL IRT model.
 * 
 * @param theta The candidate's estimated ability level
 * @param item The test item parameters
 * @returns Probability of answering correctly (0.0 to 1.0)
 */
export function calculateProbabilityComplete(theta: number, item: TestItem): number {
    const { difficulty, discrimination, guessing } = item;

    // Exponential component: e ^ (D * a * (theta - b))
    // D = 1.7 is a scaling factor commonly used in IRT to match the normal ogive model
    const D = 1.7;
    const exponent = D * discrimination * (theta - difficulty);

    // Logistic function
    const probability = guessing + (1 - guessing) / (1 + Math.exp(-exponent));

    return probability;
}

/**
 * Selects the next block of questions (Stage 2) based on Stage 1 performance.
 * The 2026 TOEFL uses Multi-Stage Adaptive Testing (MST) rather than item-level adaptive.
 * 
 * @param stage1Score The candidate's raw score from the first routing block
 * @param maxStage1Score The total possible score in the first block
 * @param availableBlocks The pool of pre-assembled Stage 2 blocks
 * @returns The best matching block ID for the candidate's current estimated ability
 */
export function routeNextStage(
    stage1Score: number,
    maxStage1Score: number,
    availableBlocks: { id: string; targetDifficulty: 'EASY' | 'MEDIUM' | 'HARD' }[]
): string {

    const percentageScore = stage1Score / maxStage1Score;

    if (percentageScore >= 0.75) {
        // Top 25% performance -> Route to Hard block for high ceiling measurement
        const hardBlock = availableBlocks.find(b => b.targetDifficulty === 'HARD');
        return hardBlock ? hardBlock.id : availableBlocks[0].id; // Fallback
    } else if (percentageScore >= 0.40) {
        // Middle performance -> Route to Medium block
        const mediumBlock = availableBlocks.find(b => b.targetDifficulty === 'MEDIUM');
        return mediumBlock ? mediumBlock.id : availableBlocks[0].id;
    } else {
        // Lower performance -> Route to Easy block to find true floor
        const easyBlock = availableBlocks.find(b => b.targetDifficulty === 'EASY');
        return easyBlock ? easyBlock.id : availableBlocks[0].id;
    }
}

/**
 * Converts final theta (ability) score to the new 2026 CEFR Band (1.0 to 6.0)
 */
export function convertThetaToCEFRBand(finalTheta: number): number {
    // Simplified conversion mapping for TOEFL 2026
    if (finalTheta >= 2.0) return 6.0;        // C2 Level
    if (finalTheta >= 1.0) return 5.0;        // C1 Level
    if (finalTheta >= 0.0) return 4.0;        // B2 Level
    if (finalTheta >= -1.0) return 3.0;       // B1 Level
    if (finalTheta >= -2.0) return 2.0;       // A2 Level
    return 1.0;                               // A1 or below
}
