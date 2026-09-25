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
}

export interface Fixture {
  id: string;
  home_team: Team;
  away_team: Team;
  league: string;
  kickoff: string;
  venue: string;
  sportybet_odds: BookmakerOdds;
  bet9ja_odds: BookmakerOdds;
  status: string;
  prediction?: PredictionDetail;
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
  sportybet_code: string;
  bet9ja_code: string;
  whatsapp_share_text: string;
  recommended_game_count_note?: string;
  leagues_covered?: string[];
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
