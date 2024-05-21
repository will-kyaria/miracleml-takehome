const getBaseUrl = () => {
    if (process.env.NODE_ENV === 'development') {
        return 'http://localhost:3000';
    }
    return 'https://your-production-url.com';
};

export const fetchTrialsBySponsor = async () => {
    const baseUrl = getBaseUrl();
    try {
        const response = await fetch(`${baseUrl}/api/trialsbysponsor`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    } catch (error: any) {
        throw new Error(`Failed to fetch trials by sponsor: ${error.message}`);
    }
};

export const fetchTrialsByCondition = async () => {
    const baseUrl = getBaseUrl();
    try {
        const response = await fetch(`${baseUrl}/api/trialsbycondition`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    } catch (error: any) {
        throw new Error(`Failed to fetch trials by condition: ${error.message}`);
    }
};
