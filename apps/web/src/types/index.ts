export type RiskLevel = 'conservative' | 'balanced' | 'aggressive';

export interface Team {
  id: string;
  name: string;
  short_code: string;
  league: string;
  rolling_xg_created: number;
  rolling_xg_conceded: number;
  form: string;
  key_injuries: string[];
  /** Club crest URL from the fixture feed; absent when the feed did not report one. */
  crest?: string | null;
}

export interface BookmakerOdds {
  bookmaker: string;
  home_win: number;
  draw: number;
  away_win: number;
  over_1_5?: number;
  over_2_5?: number;
  under_2_5?: number;
  btts_yes?: number;
  double_chance_1x?: number;
  double_chance_x2?: number;
}

export interface ValueBetItem {
  market: string;
  market_name: string;
  selection: string;
  bookmaker: string;
  market_odds: number;
  fair_odds: number;
  model_probability: number;
  implied_probability: number;
  expected_value_pct: number;
  recommended_stake_pct: number;
  recommended_stake_ngn: number;
  confidence_tier: string;
  reasoning: string;
}

export interface PredictionDetail {
  home_team: string;
  away_team: string;
  league: string;
  kickoff_time: string;
  expected_goals_home: number;
  expected_goals_away: number;
  prob_home_win: number;
  prob_draw: number;
  prob_away_win: number;
  prob_over_1_5: number;
  prob_over_2_5: number;
  prob_under_2_5: number;
  prob_btts: number;
  fair_odds_home: number;
  fair_odds_draw: number;
  fair_odds_away: number;
  top_exact_scores: Record<string, number>;
  gemini_tactical_summary: string;
  gemini_lineup_risk: string;
  value_bets: ValueBetItem[];
  likely_winner_team?: string;
  likely_winner_prob?: number;
  likely_winner_confidence?: string;
  statistical_verdict?: string;
  recommended_safe_pick?: string;
  recommended_safe_odds?: number;
  key_factors?: string[];
  prediction_source?: string;
}

export interface HeadToHeadMatch {
  date: string;
  competition: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  winner: 'home' | 'away' | 'draw';
}

export interface HeadToHeadStats {
  total_meetings: number;
  home_team_wins: number;
  draws: number;
  away_team_wins: number;
  home_goals_total: number;
  away_goals_total: number;
  last_matches: HeadToHeadMatch[];
  summary: string;
}

export interface Fixture {
  id: string;
  div?: string;
  home_team: Team;
  away_team: Team;
  league: string;
  /** Competition emblem URL from the fixture feed, when known. */
  league_crest?: string | null;
  kickoff: string;
  match_date?: string;
  match_time?: string;
  venue: string;
  sportybet_odds: BookmakerOdds;
  bet9ja_odds: BookmakerOdds;
  status: string;
  is_upcoming?: boolean;
  kickoff_timestamp?: string;
  match_status?: string;
  prediction?: PredictionDetail;
  h2h?: HeadToHeadStats;
}

export interface AccumulatorLeg {
  fixture_id: string;
  match_name: string;
  market: string;
  odds: number;
  model_probability: number;
  ev_pct: number;
  risk_assessment: string;
  safer_alternative?: string;
  league?: string;
  likely_winner?: string;
  bookmaker_search_text?: string;
  kickoff?: string;
}

export interface AccumulatorResponse {
  ticket_type: string;
  total_odds: number;
  win_probability: number;
  recommended_stake_ngn: number;
  potential_payout_ngn: number;
  legs: AccumulatorLeg[];
  cut_1_insured: boolean;
  cut_1_warning?: string;
  sportybet_code?: string | null;
  bet9ja_code?: string | null;
  whatsapp_share_text: string;
  recommended_game_count_note?: string;
  leagues_covered?: string[];
  match_search_list?: string;
  is_upcoming_verified?: boolean;
}

export interface TrackRecordEntry {
  id: string;
  date: string;
  match: string;
  prediction: string;
  odds: number;
  stake_ngn: number;
  result: 'won' | 'lost' | 'void' | 'pending';
  return_ngn: number;
  profit_ngn: number;
  pnl_running_roi: number;
  ai_post_mortem?: string;
}

export interface TrackRecordStats {
  total_bets: number;
  wins: number;
  losses: number;
  voids: number;
  win_rate_pct: number;
  total_staked_ngn: number;
  total_returned_ngn: number;
  net_profit_ngn: number;
  roi_pct: number;
  current_winning_streak: number;
  entries: TrackRecordEntry[];
}

export interface ScoreSummary {
  n: number;
  accuracy: number;
  log_loss: number;
  brier: number;
}

export interface CalibrationRow {
  bucket: string;
  matches: number;
  predicted: number;
  actual: number;
}

export interface ModelReport {
  trained_at: string;
  trained_through: string;
  primary_variant: string;
  variants: Record<string, { algorithm: string; matches_used: number }>;
  splits: { burn_in: string; validation: string; test: string[] };
  test: Record<string, ScoreSummary>;
  test_calibration: CalibrationRow[];
  test_top_leagues: Record<string, Record<string, ScoreSummary>>;
  value_policy: { enabled: boolean; reason?: string; min_ev?: number };
}

export interface ChainVerification {
  valid: boolean;
  entries: number;
  first_broken_seq: number | null;
  latest_hash?: string;
}

export interface AppUser {
  email: string;
  name: string | null;
  picture: string | null;
  role: "admin" | "user";
}

export interface SavedFixture {
  fixture_id: string;
  saved_at: string;
  league: string;
  league_crest: string | null;
  home_team: string;
  away_team: string;
  home_crest: string | null;
  away_crest: string | null;
  kickoff_utc: string | null;
  p_home: number;
  p_draw: number;
  p_away: number;
  pick: "1" | "X" | "2";
  status: "upcoming" | "awaiting_result" | "finished";
  home_goals: number | null;
  away_goals: number | null;
  actual: "1" | "X" | "2" | null;
  pick_correct: boolean | null;
}

export interface PredictionReport {
  generated_at: string;
  summary: {
    locked: number; graded: number; pending: number; voided: number; correct: number;
    accuracy_pct: number; avg_confidence_pct: number; brier: number; baseline_brier: number; log_loss: number;
  };
  calibration: { label: string; count: number; avg_predicted_pct: number; actual_pct: number }[];
  leagues: { league: string; graded: number; correct: number; accuracy_pct: number }[];
  matches: {
    id: string; kickoff_utc: string; league: string; home_team: string; away_team: string;
    p_home: number; p_draw: number; p_away: number; pick: "1" | "X" | "2";
    status: "pending" | "void" | "graded";
    home_goals: number | null; away_goals: number | null; actual: "1" | "X" | "2" | null; correct: boolean | null;
  }[];
}
