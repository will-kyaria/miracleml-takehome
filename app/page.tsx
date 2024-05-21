'use server'
import { fetchTrialsByCondition, fetchTrialsBySponsor } from "./actions";
import BarChartComponent from "./components/barchart";
import { cache } from "react";

const loadTrialsBySponsor = cache(async () => {
  return await fetchTrialsBySponsor();
});

const loadTrialsByCondition = cache(async () => {
  return await fetchTrialsByCondition();
});

export default async function Home() {
  const sponsorTrials = await loadTrialsBySponsor();
  const conditionTrials = await loadTrialsByCondition();

  return (
    <main className="flex h-screen flex-col items-center justify-between p-24 bg-gray-100">
      <div className="flex flex-col md:flex-row w-full h-full space-y-6 md:space-y-0 md:space-x-6">
        <div className="flex-1">
          <BarChartComponent
            data={sponsorTrials.trials_by_sponsor}
            dataKeyX="sponsor"
            dataKeyY="count"
            title="Clinical Trials Data by Sponsor"
          />
        </div>
        <div className="flex-1">
          <BarChartComponent
            data={conditionTrials.trials_by_condition}
            dataKeyX="condition"
            dataKeyY="count"
            title="Clinical Trials Data by Condition"
          />
        </div>
      </div>
    </main>
  );
}
