import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router } from "./_core/trpc";
import {
  generateResearchIdeas,
  analyzeTrends,
  searchArxivPapers,
} from "./research";

export const appRouter = router({
  system: systemRouter,

  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  research: router({
    generateIdeas: publicProcedure
      .input((val: any) => val)
      .mutation(({ input }) => generateResearchIdeas(input)),
    analyzeTrends: publicProcedure
      .input((val: any) => val)
      .mutation(({ input }) => analyzeTrends(input)),
    searchPapers: publicProcedure
      .input((val: any) => val)
      .mutation(({ input }) => searchArxivPapers(input))
  }),
});

export type AppRouter = typeof appRouter;
