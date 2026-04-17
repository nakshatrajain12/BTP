import useSWR from 'swr';
import { api } from '@/lib/api';

export function useDashboard() {
  const { data: summary, error: summaryError, isLoading: summaryLoading } = useSWR('/analytics/summary', () => api.getSummary());
  const { data: funding, error: fundingError, isLoading: fundingLoading } = useSWR('/analytics/funding-by-ministry', () => api.getFundingByMinistry());
  const { data: sector, error: sectorError, isLoading: sectorLoading } = useSWR('/analytics/sector-distribution', () => api.getSectorDistribution());
  const { data: alerts, error: alertsError, isLoading: alertsLoading } = useSWR('/alerts/recent', () => api.getRecentAlerts());
  const { data: pipeline, error: pipelineError, isLoading: pipelineLoading } = useSWR('/pipeline/status', () => api.getPipelineStatus());

  return {
    summary,
    funding,
    sector,
    alerts: alerts?.alerts || [],
    pipeline,
    isLoading: summaryLoading || fundingLoading || alertsLoading || pipelineLoading || sectorLoading,
    isError: summaryError || fundingError || alertsError || pipelineError || sectorError
  };
}

// Simulated profile matching the new user signups format.
export function useRecommendations() {
  // Try to load simulated profile from local storage, fallback to general if null.
  // In a real app we'd fetch the Supabase auth session then its profile.
  const profile = { sector: 'Deeptech', stage: 'Idea', state: 'Pan-India' };
  
  const { data, error, isLoading } = useSWR(['/recommend', profile], () => api.getRecommendations(profile));
  
  return {
    recommendations: data?.recommendations || [],
    isLoading,
    isError: Boolean(error)
  }
}
