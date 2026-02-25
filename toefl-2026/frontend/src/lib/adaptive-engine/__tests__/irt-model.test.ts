import {
    calculateProbabilityComplete,
    routeNextStage,
    convertThetaToCEFRBand,
    TestItem
} from '../irt-model';

describe('IRT Model Mathematical Engine', () => {

    const easyItem: TestItem = { id: 'easy_1', difficulty: -2.0, discrimination: 1.0, guessing: 0.25 };
    const mediumItem: TestItem = { id: 'medium_1', difficulty: 0.0, discrimination: 1.5, guessing: 0.25 };
    const hardItem: TestItem = { id: 'hard_1', difficulty: 2.0, discrimination: 2.0, guessing: 0.20 };

    describe('calculateProbabilityComplete', () => {
        it('returns a high probability for a high-ability candidate on an easy item', () => {
            const prob = calculateProbabilityComplete(2.0, easyItem);
            expect(prob).toBeGreaterThan(0.9);
        });

        it('returns a probability near the guessing parameter for a low-ability candidate on a hard item', () => {
            const prob = calculateProbabilityComplete(-2.0, hardItem);
            // Low theta (-2.0), Hard item (2.0) -> exponent is strongly negative
            // Probability should be very close to the guessing param (0.20)
            expect(prob).toBeCloseTo(0.20, 1);
        });
    });

    describe('routeNextStage', () => {
        const blocks = [
            { id: 'block_e', targetDifficulty: 'EASY' as const },
            { id: 'block_m', targetDifficulty: 'MEDIUM' as const },
            { id: 'block_h', targetDifficulty: 'HARD' as const }
        ];

        it('routes high performers to the HARD block', () => {
            expect(routeNextStage(9, 10, blocks)).toBe('block_h');
            expect(routeNextStage(8, 10, blocks)).toBe('block_h');
        });

        it('routes average performers to the MEDIUM block', () => {
            expect(routeNextStage(5, 10, blocks)).toBe('block_m');
            expect(routeNextStage(6, 10, blocks)).toBe('block_m');
        });

        it('routes low performers to the EASY block', () => {
            expect(routeNextStage(2, 10, blocks)).toBe('block_e');
            expect(routeNextStage(3, 10, blocks)).toBe('block_e');
        });
    });

    describe('convertThetaToCEFRBand', () => {
        it('correctly maps Ability Theta to the 2026 CEFR Band', () => {
            expect(convertThetaToCEFRBand(2.5)).toBe(6.0); // C2
            expect(convertThetaToCEFRBand(1.5)).toBe(5.0); // C1
            expect(convertThetaToCEFRBand(0.5)).toBe(4.0); // B2
            expect(convertThetaToCEFRBand(-0.5)).toBe(3.0); // B1
            expect(convertThetaToCEFRBand(-1.5)).toBe(2.0); // A2
            expect(convertThetaToCEFRBand(-2.5)).toBe(1.0); // A1
        });
    });
});
